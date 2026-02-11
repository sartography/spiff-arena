import json
import os
import uuid
from typing import Any
from typing import TypedDict

import flask.wrappers
import sentry_sdk
from flask import Blueprint
from flask import current_app
from flask import g
from flask import jsonify
from flask import make_response
from flask.wrappers import Response
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore
from SpiffWorkflow.util.task import TaskState  # type: ignore
from sqlalchemy import and_
from sqlalchemy import or_

from spiffworkflow_backend.background_processing.celery_tasks.process_instance_task_producer import (
    queue_enabled_for_process_model,
)
from spiffworkflow_backend.background_processing.celery_tasks.process_instance_task_producer import (
    queue_process_instance_if_appropriate,
)
from spiffworkflow_backend.data_migrations.process_instance_migrator import ProcessInstanceMigrator
from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.exceptions.error import HumanTaskAlreadyCompletedError
from spiffworkflow_backend.exceptions.error import HumanTaskNotFoundError
from spiffworkflow_backend.exceptions.error import UserDoesNotHaveAccessToTaskError
from spiffworkflow_backend.exceptions.process_entity_not_found_error import ProcessEntityNotFoundError
from spiffworkflow_backend.models.bpmn_process import BpmnProcessModel
from spiffworkflow_backend.models.bpmn_process_definition import BpmnProcessDefinitionModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.human_task_user import HumanTaskUserModel
from spiffworkflow_backend.models.json_data import JsonDataModel
from spiffworkflow_backend.models.principal import PrincipalModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
from spiffworkflow_backend.models.process_instance_file_data import ProcessInstanceFileDataModel
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.models.reference_cache import ReferenceCacheModel
from spiffworkflow_backend.models.task import TaskModel
from spiffworkflow_backend.services.authorization_service import AuthorizationService
from spiffworkflow_backend.services.file_system_service import FileSystemService
from spiffworkflow_backend.services.git_service import GitCommandError
from spiffworkflow_backend.services.git_service import GitService
from spiffworkflow_backend.services.jinja_service import JinjaService
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.process_instance_queue_service import ProcessInstanceQueueService
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.reference_cache_service import ReferenceCacheService
from spiffworkflow_backend.services.spec_file_service import SpecFileService
from spiffworkflow_backend.services.task_service import TaskModelError
from spiffworkflow_backend.services.task_service import TaskService
from spiffworkflow_backend.services.workflow_spec_service import WorkflowSpecService

process_api_blueprint = Blueprint("process_api", __name__)


class TaskDataSelectOption(TypedDict):
    value: str
    label: str


class ReactJsonSchemaSelectOption(TypedDict):
    type: str
    title: str
    enum: list[str]


def permissions_check(body: dict[str, dict[str, list[str]]]) -> flask.wrappers.Response:
    if "requests_to_check" not in body:
        raise (
            ApiError(
                error_code="could_not_requests_to_check",
                message="The key 'requests_to_check' not found at root of request body.",
                status_code=400,
            )
        )
    response_dict: dict[str, dict[str, bool]] = {}
    requests_to_check = body["requests_to_check"]

    user = g.user
    permission_assignments = AuthorizationService.all_permission_assignments_for_user(user=user)

    for target_uri, http_methods in requests_to_check.items():
        if target_uri not in response_dict:
            response_dict[target_uri] = {}

        for http_method in http_methods:
            permission_string = AuthorizationService.get_permission_from_http_method(http_method)
            if permission_string:
                has_permission = AuthorizationService.permission_assignments_include(
                    permission_assignments=permission_assignments,
                    permission=permission_string,
                    target_uri=target_uri,
                )
                response_dict[target_uri][http_method] = has_permission

    return make_response(jsonify({"results": response_dict}), 200)


def process_list() -> Any:
    """Returns a list of all known processes.

    This includes processes that are not the
    primary process - helpful for finding possible call activities.
    """
    references = ReferenceCacheModel.basic_query().filter_by(type="process").all()
    process_model_identifiers = [r.relative_location for r in references]
    permitted_process_model_identifiers = ProcessModelService.process_model_identifiers_with_permission_for_user(
        user=g.user,
        permission_to_check="create",
        permission_base_uri=f"{current_app.config['SPIFFWORKFLOW_BACKEND_API_PATH_PREFIX']}/process-instances",
        process_model_identifiers=process_model_identifiers,
    )
    permitted_references = []
    for spec_reference in references:
        if spec_reference.relative_location in permitted_process_model_identifiers:
            permitted_references.append(spec_reference)
    return [s.to_dict() for s in permitted_references]


# if we pass in bpmn_process_identifiers of [a], a is "called" and we want to find which processes are *callers* of a
def process_caller_list(bpmn_process_identifiers: list[str]) -> Any:
    references = ReferenceCacheService.get_reference_cache_entries_calling_process(bpmn_process_identifiers)
    return [s.to_dict() for s in references]


def _get_bpmn_process_with_data_object(
    process_data_identifier: str,
    bpmn_processes_by_id: dict[int, BpmnProcessModel],
    bpmn_process_definitions_by_id: dict[int, BpmnProcessDefinitionModel],
    current_bp: BpmnProcessModel,
) -> Any:
    current_bpd = bpmn_process_definitions_by_id[current_bp.bpmn_process_definition_id]
    if "data_objects" in current_bpd.properties_json and process_data_identifier in current_bpd.properties_json["data_objects"]:
        return current_bp
    elif current_bp.direct_parent_process_id in bpmn_processes_by_id:
        return _get_bpmn_process_with_data_object(
            process_data_identifier,
            bpmn_processes_by_id,
            bpmn_process_definitions_by_id,
            bpmn_processes_by_id[current_bp.direct_parent_process_id],
        )
    else:
        return current_bp


def _get_data_object_from_bpmn_process(
    process_data_identifier: str,
    bpmn_process: BpmnProcessModel,
    bpmn_process_guid: str | None,
    process_instance: ProcessInstanceModel,
) -> Any:
    bpmn_process_data = JsonDataModel.find_data_dict_by_hash(bpmn_process.json_data_hash)
    if bpmn_process_data is None:
        raise ApiError(
            error_code="bpmn_process_data_not_found",
            message=f"Cannot find a bpmn process data with guid '{bpmn_process_guid}' for process instance {process_instance.id}",
            status_code=404,
        )

    data_objects = bpmn_process_data.get("data_objects", {})
    return data_objects.get(process_data_identifier)


def _process_data_fetcher(
    process_instance_id: int,
    process_data_identifier: str,
    category: str,
    bpmn_process_guid: str | None = None,
    process_identifier: str | None = None,
) -> flask.wrappers.Response:
    process_instance = _find_process_instance_by_id_or_raise(process_instance_id)
    if bpmn_process_guid is not None:
        bpmn_process = BpmnProcessModel.query.filter_by(guid=bpmn_process_guid).first()
    else:
        bpmn_process = process_instance.bpmn_process
    if bpmn_process is None:
        raise ApiError(
            error_code="bpmn_process_not_found",
            message=f"Cannot find a bpmn process with guid '{bpmn_process_guid}' for process instance {process_instance.id}",
            status_code=404,
        )

    data_object_value = _get_data_object_from_bpmn_process(
        process_data_identifier=process_data_identifier,
        bpmn_process=bpmn_process,
        bpmn_process_guid=bpmn_process_guid,
        process_instance=process_instance,
    )

    # if the data object value cannot be found with the given bpmn process then attempt to get it from the parent that defines it
    if data_object_value is None:
        all_bpmn_processes = None
        if bpmn_process.top_level_process_id is not None:
            all_bpmn_processes = BpmnProcessModel.query.filter(
                or_(
                    BpmnProcessModel.top_level_process_id == bpmn_process.top_level_process_id,
                    BpmnProcessModel.id == bpmn_process.top_level_process_id,
                )
            ).all()
            all_bpmn_def_ids = [bp.bpmn_process_definition_id for bp in all_bpmn_processes]
            all_bpmn_process_definitions = BpmnProcessDefinitionModel.query.filter(
                BpmnProcessDefinitionModel.id.in_(all_bpmn_def_ids)  # type: ignore
            ).all()
            bpmn_processes_by_id = {bp.id: bp for bp in all_bpmn_processes}
            bpmn_process_definitions_by_id = {bpd.id: bpd for bpd in all_bpmn_process_definitions}
            bp = _get_bpmn_process_with_data_object(
                process_data_identifier, bpmn_processes_by_id, bpmn_process_definitions_by_id, bpmn_process
            )
            data_object_value = _get_data_object_from_bpmn_process(
                process_data_identifier=process_data_identifier,
                bpmn_process=bp,
                bpmn_process_guid=bpmn_process_guid,
                process_instance=process_instance,
            )

    if data_object_value is None:
        raise ApiError(
            error_code="data_object_not_found",
            message=(
                f"Cannot find a data object with identifier '{process_data_identifier}' for bpmn process"
                f" '{bpmn_process.bpmn_process_definition.bpmn_identifier}' in process instance {process_instance.id}"
            ),
            status_code=404,
        )

    if hasattr(data_object_value, "category") and data_object_value.category is not None:
        if data_object_value.category != category:
            raise ApiError(
                error_code="data_object_category_mismatch",
                message=f"The desired data object has category '{data_object_value.category}' "
                "instead of the expected '{category}'",
                status_code=400,
            )

    return make_response(
        jsonify(
            {
                "process_data_identifier": process_data_identifier,
                "process_data_value": data_object_value,
            }
        ),
        200,
    )


def process_data_show(
    category: str,
    process_instance_id: int,
    process_data_identifier: str,
    modified_process_model_identifier: str,
    bpmn_process_guid: str | None = None,
    process_identifier: str | None = None,
) -> flask.wrappers.Response:
    return _process_data_fetcher(
        process_instance_id=process_instance_id,
        process_data_identifier=process_data_identifier,
        category=category,
        bpmn_process_guid=bpmn_process_guid,
        process_identifier=process_identifier,
    )


def process_data_file_download(
    process_instance_id: int,
    process_data_identifier: str,
    modified_process_model_identifier: str,
    bpmn_process_guid: str | None = None,
    process_identifier: str | None = None,
) -> flask.wrappers.Response:
    file_data = ProcessInstanceFileDataModel.query.filter_by(
        digest=process_data_identifier,
        process_instance_id=process_instance_id,
    ).first()
    if file_data is None:
        raise ApiError(
            error_code="process_instance_file_data_not_found",
            message=f"Could not find file data related to the digest: {process_data_identifier}",
        )
    mimetype = file_data.mimetype
    filename = file_data.filename
    file_contents = file_data.get_contents()

    return Response(
        file_contents,
        mimetype=mimetype,
        headers={"Content-disposition": f"attachment; filename={filename}"},
    )


def _get_required_parameter_or_raise(parameters: list[str], post_body: dict[str, Any]) -> tuple[Any, str | None]:
    return_value = None
    parameter_name = None

    for parameter in parameters:
        if parameter in post_body:
            parameter_name = parameter
            return_value = post_body[parameter]

    if return_value is None or return_value == "":
        raise (
            ApiError(
                error_code="missing_required_parameter",
                message=f"Parameter is missing from json request body: {parameters}",
                status_code=400,
            )
        )

    return return_value, parameter_name


def _commit_and_push_to_git(message: str) -> None:
    if current_app.config["SPIFFWORKFLOW_BACKEND_GIT_COMMIT_ON_SAVE"]:
        git_output = GitService.commit(message=message)
        current_app.logger.info(f"git output: {git_output}")
    else:
        current_app.logger.info("Git commit on save is disabled")


def _un_modify_modified_process_model_id(modified_process_model_identifier: str) -> str:
    return modified_process_model_identifier.replace(":", "/")


def _find_process_instance_by_id_or_raise(
    process_instance_id: int,
) -> ProcessInstanceModel:
    process_instance_query = ProcessInstanceModel.query.filter_by(id=process_instance_id)

    # we had a frustrating session trying to do joins and access columns from two tables. here's some notes for our future selves:
    # this returns an object that allows you to do: process_instance.UserModel.username
    # process_instance = db.session.query(ProcessInstanceModel, UserModel).filter_by(id=process_instance_id).first()
    # you can also use splat with add_columns, but it still didn't ultimately give us access to the process instance
    # attributes or username like we wanted:
    # process_instance_query.join(UserModel).add_columns(*ProcessInstanceModel.__table__.columns, UserModel.username)

    process_instance = process_instance_query.first()
    if process_instance is None:
        raise (
            ApiError(
                error_code="process_instance_cannot_be_found",
                message=f"Process instance cannot be found: {process_instance_id}",
                status_code=400,
            )
        )
    return process_instance  # type: ignore


# process_model_id uses forward slashes on all OSes
# this seems to return an object where process_model.id has backslashes on windows
def _get_process_model(process_model_id: str) -> ProcessModelInfo:
    process_model = None
    try:
        process_model = ProcessModelService.get_process_model(process_model_id)
    except ProcessEntityNotFoundError as exception:
        raise (
            ApiError(
                error_code="process_model_cannot_be_found",
                message=f"Process model cannot be found: {process_model_id}",
                status_code=400,
            )
        ) from exception

    return process_model


def _find_principal_or_raise() -> PrincipalModel:
    principal = PrincipalModel.query.filter_by(user_id=g.user.id).first()
    if principal is None:
        raise (
            ApiError(
                error_code="principal_not_found",
                message=f"Principal not found from user id: {g.user.id}",
                status_code=400,
            )
        )
    return principal  # type: ignore


def _find_process_instance_for_me_or_raise(
    process_instance_id: int,
    include_actions: bool = False,
) -> ProcessInstanceModel:
    process_instance: ProcessInstanceModel | None = (
        ProcessInstanceModel.query.filter_by(id=process_instance_id)
        .outerjoin(HumanTaskModel)
        .outerjoin(
            HumanTaskUserModel,
            and_(
                HumanTaskModel.id == HumanTaskUserModel.human_task_id,
                HumanTaskUserModel.user_id == g.user.id,
            ),
        )
        .filter(
            or_(
                # you were allowed to complete it
                HumanTaskUserModel.id.is_not(None),
                # or you completed it (which admins can do even if it wasn't assigned via HumanTaskUserModel)
                HumanTaskModel.completed_by_user_id == g.user.id,
                # or you started it
                ProcessInstanceModel.process_initiator_id == g.user.id,
            )
        )
        .first()
    )

    if process_instance is None:
        raise (
            ApiError(
                error_code="process_instance_cannot_be_found",
                message=f"Process instance with id {process_instance_id} cannot be found that is associated with you.",
                status_code=400,
            )
        )

    if include_actions:
        modified_process_model_identifier = ProcessModelInfo.modify_process_identifier_for_path_param(
            process_instance.process_model_identifier
        )
        api_path_prefix = current_app.config["SPIFFWORKFLOW_BACKEND_API_PATH_PREFIX"]
        target_uri = f"{api_path_prefix}/process-instances/for-me/{modified_process_model_identifier}/{process_instance.id}"
        has_permission = AuthorizationService.user_has_permission(
            user=g.user,
            permission="read",
            target_uri=target_uri,
        )
        if has_permission:
            process_instance.actions = {"read": {"path": target_uri, "method": "GET"}}

    return process_instance


def _get_process_model_for_instantiation(
    process_model_identifier: str,
) -> ProcessModelInfo:
    process_model = _get_process_model(process_model_identifier)
    if process_model.primary_file_name is None:
        raise ApiError(
            error_code="process_model_missing_primary_bpmn_file",
            message=(
                f"Process Model '{process_model_identifier}' does not have a primary"
                " bpmn file. One must be set in order to instantiate this model."
            ),
            status_code=400,
        )
    return process_model


def _prepare_form_data(
    form_file: str, process_model: ProcessModelInfo, task_model: TaskModel | None = None, revision: str | None = None
) -> dict:
    try:
        form_contents = GitService.get_file_contents_for_revision_if_git_revision(
            process_model=process_model,
            revision=revision,
            file_name=form_file,
        )
    except GitCommandError as exception:
        raise (
            ApiError(
                error_code="git_error_loading_form",
                message=(
                    f"Could not load form schema from: {form_file}. Was git history rewritten such that revision"
                    f" '{revision}' no longer exists? Error was: {str(exception)}"
                ),
                status_code=400,
            )
        ) from exception

    if task_model and task_model.data is not None:
        try:
            form_contents = JinjaService.render_jinja_template(form_contents, task=task_model)
        except TaskModelError as wfe:
            wfe.add_note(f"Error in Json Form File '{form_file}'")
            api_error = ApiError.from_workflow_exception("instructions_error", str(wfe), exp=wfe)
            api_error.file_name = form_file
            raise api_error from wfe

    try:
        # form_contents is a str
        hot_dict: dict = json.loads(form_contents)
        return hot_dict
    except Exception as exception:
        raise (
            ApiError(
                error_code="error_loading_form",
                message=f"Could not load form schema from: {form_file}. Error was: {str(exception)}",
                status_code=400,
            )
        ) from exception


def _task_submit_shared(
    process_instance_id: int,
    task_guid: str,
    body: dict[str, Any],
    execution_mode: str | None = None,
) -> dict:
    principal = _find_principal_or_raise()
    process_instance = _find_process_instance_by_id_or_raise(process_instance_id)
    if not process_instance.can_submit_task():
        raise ApiError(
            error_code="process_instance_not_runnable",
            message=(
                f"Process Instance ({process_instance.id}) has status "
                f"{process_instance.status} which does not allow tasks to be submitted."
            ),
            status_code=400,
        )

    AuthorizationService.assert_user_can_complete_human_task(process_instance.id, task_guid, principal.user)

    with sentry_sdk.start_span(op="task", name="complete_form_task"):
        with ProcessInstanceQueueService.dequeued(process_instance, max_attempts=3):
            if ProcessInstanceMigrator.run(process_instance):
                # Refresh the process instance to get any updates from migration
                db.session.refresh(process_instance)

            processor = ProcessInstanceProcessor(
                process_instance, workflow_completed_handler=ProcessInstanceService.schedule_next_process_model_cycle
            )
            spiff_task = _get_spiff_task_from_processor(task_guid, processor)

            if spiff_task.state != TaskState.READY:
                raise (
                    ApiError(
                        error_code="invalid_state",
                        message="You may not update a task unless it is in the READY state.",
                        status_code=400,
                    )
                )

            human_task = _find_human_task_or_raise(
                process_instance_id=process_instance_id,
                task_guid=task_guid,
                only_tasks_that_can_be_completed=True,
            )

            ProcessInstanceService.complete_form_task(
                processor=processor,
                spiff_task=spiff_task,
                data=body,
                user=g.user,
                human_task=human_task,
                execution_mode=execution_mode,
            )
        queue_process_instance_if_appropriate(process_instance, execution_mode)

    # currently task_model has the potential to be None. This should be removable once
    # we backfill the human_task table for task_guid and make that column not nullable
    task_model: TaskModel | None = human_task.task_model
    if task_model is None:
        task_model = TaskModel.query.filter_by(guid=human_task.task_id).first()

    # delete draft data when we submit a task to ensure cycling back to the task contains the
    # most up-to-date data
    task_draft_data = TaskService.task_draft_data_from_task_model(task_model)
    if task_draft_data is not None:
        db.session.delete(task_draft_data)
        db.session.commit()

    next_human_task_assigned_to_me = TaskService.next_human_task_for_user(process_instance_id, principal.user_id)
    if next_human_task_assigned_to_me:
        return {"next_task_assigned_to_me": HumanTaskModel.to_task(next_human_task_assigned_to_me)}

    # a guest user completed a task, it has a guest_confirmation message to display to them,
    # and there is nothing else for them to do
    spiff_task_extensions = spiff_task.task_spec.extensions
    if "guestConfirmation" in spiff_task_extensions and spiff_task_extensions["guestConfirmation"]:
        guest_confirmation = JinjaService.render_jinja_template(spiff_task_extensions["guestConfirmation"], task_model)
        return {"guest_confirmation": guest_confirmation}

    if processor.next_task():
        task = ProcessInstanceService.spiff_task_to_api_task(processor, processor.next_task())
        task.process_model_uses_queued_execution = queue_enabled_for_process_model()
        return {"next_task": task}

    # next_task always returns something, even if the instance is complete, so we never get here
    return {
        "ok": True,
        "process_model_identifier": process_instance.process_model_identifier,
        "process_instance_id": process_instance_id,
    }


def _find_human_task_or_raise(
    process_instance_id: int,
    task_guid: str,
    only_tasks_that_can_be_completed: bool = False,
) -> HumanTaskModel:
    if only_tasks_that_can_be_completed:
        human_task_query = HumanTaskModel.query.filter_by(
            process_instance_id=process_instance_id,
            task_id=task_guid,
            completed=False,
        )
    else:
        human_task_query = HumanTaskModel.query.filter_by(process_instance_id=process_instance_id, task_id=task_guid)

    human_task: HumanTaskModel | None = human_task_query.first()
    if human_task is None:
        raise (
            ApiError(
                error_code="no_human_task",
                message=f"Cannot find a task to complete for task id '{task_guid}' and process instance {process_instance_id}.",
                status_code=500,
            )
        )
    return human_task


def _get_spiff_task_from_processor(
    task_guid: str,
    processor: ProcessInstanceProcessor,
) -> SpiffTask:
    task_uuid = uuid.UUID(task_guid)
    spiff_task = processor.bpmn_process_instance.get_task_from_id(task_uuid)

    if spiff_task is None:
        raise (
            ApiError(
                error_code="empty_task",
                message="Processor failed to obtain task.",
                status_code=500,
            )
        )
    return spiff_task


def _get_task_model_from_guid_or_raise(task_guid: str, process_instance_id: int | None) -> TaskModel:
    task_model_query = TaskModel.query.filter_by(guid=task_guid)
    if process_instance_id is not None:
        task_model_query = task_model_query.filter_by(process_instance_id=process_instance_id)
    task_model: TaskModel | None = task_model_query.first()
    if task_model is None:
        raise ApiError(
            error_code="task_not_found",
            message=f"Cannot find a task with guid '{task_guid}' for process instance '{process_instance_id}'",
            status_code=400,
        )
    return task_model


def _get_task_model_for_request(
    process_instance_id: int,
    task_guid: str = "next",
    with_form_data: bool = False,
) -> TaskModel:
    process_instance = _find_process_instance_by_id_or_raise(process_instance_id)

    if process_instance.status == ProcessInstanceStatus.suspended.value:
        raise ApiError(
            error_code="error_suspended",
            message="The process instance is suspended",
            status_code=400,
        )

    process_model = _get_process_model(
        process_instance.process_model_identifier,
    )

    task_model = _get_task_model_from_guid_or_raise(task_guid, process_instance_id)
    task_definition = task_model.task_definition

    can_complete = False
    try:
        AuthorizationService.assert_user_can_complete_human_task(process_instance.id, task_model.guid, g.user)
        can_complete = True
    except (
        HumanTaskNotFoundError,
        UserDoesNotHaveAccessToTaskError,
        HumanTaskAlreadyCompletedError,
    ):
        can_complete = False

    task_model.process_model_display_name = process_model.display_name
    task_model.process_model_identifier = process_model.id
    task_model.typename = task_definition.typename
    task_model.can_complete = can_complete
    task_model.name_for_display = TaskService.get_name_for_display(task_definition)
    extensions = TaskService.get_extensions_from_task_model(task_model)

    if with_form_data:
        task_process_identifier = task_model.bpmn_process.bpmn_process_definition.bpmn_identifier
        process_model_with_form = process_model

        refs = SpecFileService.get_references_for_process(process_model_with_form)
        all_processes = [i.identifier for i in refs]
        if task_process_identifier not in all_processes:
            top_bpmn_process = TaskService.bpmn_process_for_called_activity_or_top_level_process(task_model)
            bpmn_file_full_path = WorkflowSpecService.bpmn_file_full_path_from_bpmn_process_identifier(
                top_bpmn_process.bpmn_process_definition.bpmn_identifier
            )
            relative_path = os.path.relpath(bpmn_file_full_path, start=FileSystemService.root_path())
            process_model_relative_path = os.path.dirname(relative_path)
            process_model_with_form = ProcessModelService.get_process_model_from_relative_path(process_model_relative_path)

        form_schema_file_name = ""
        form_ui_schema_file_name = ""
        task_model.signal_buttons = TaskService.get_ready_signals_with_button_labels(process_instance_id, task_model.guid)

        if "properties" in extensions:
            properties = extensions["properties"]
            if "formJsonSchemaFilename" in properties:
                form_schema_file_name = properties["formJsonSchemaFilename"]
            if "formUiSchemaFilename" in properties:
                form_ui_schema_file_name = properties["formUiSchemaFilename"]

        task_draft_data = TaskService.task_draft_data_from_task_model(task_model)

        saved_form_data = None
        if task_draft_data is not None:
            saved_form_data = task_draft_data.get_saved_form_data()

        task_model.data = task_model.get_data()
        task_model.saved_form_data = saved_form_data
        if task_definition.typename == "UserTask":
            if not form_schema_file_name:
                raise (
                    ApiError(
                        error_code="missing_form_file",
                        message=f"Cannot find a form file for process_instance_id: {process_instance_id}, task_guid: {task_guid}",
                        status_code=400,
                    )
                )

            form_dict = _prepare_form_data(
                form_file=form_schema_file_name,
                task_model=task_model,
                process_model=process_model_with_form,
                revision=process_instance.bpmn_version_control_identifier,
            )
            _update_form_schema_with_task_data_as_needed(form_dict, task_model.data)
            task_model.form_schema = form_dict

            if form_ui_schema_file_name:
                ui_form_contents = _prepare_form_data(
                    form_file=form_ui_schema_file_name,
                    task_model=task_model,
                    process_model=process_model_with_form,
                    revision=process_instance.bpmn_version_control_identifier,
                )
                task_model.form_ui_schema = ui_form_contents
            else:
                task_model.form_ui_schema = {}
            _munge_form_ui_schema_based_on_hidden_fields_in_task_data(task_model.form_ui_schema, task_model.data)

            subset_var = extensions.get("variableName")
            if subset_var:
                task_model.data = {subset_var: task_model.data.get(subset_var, {})}

        # it should be safe to add instructions to the task spec here since we are never commiting it back to the db
        extensions["instructionsForEndUser"] = JinjaService.render_instructions_for_end_user(task_model, extensions)

    task_model.extensions = extensions
    return task_model


# originally from: https://bitcoden.com/answers/python-nested-dictionary-update-value-where-any-nested-key-matches
def _update_form_schema_with_task_data_as_needed(in_dict: dict, task_data: dict) -> None:
    for k, value in in_dict.items():
        if k in {"anyOf", "items"}:
            # value will look like the array on the right of "anyOf": ["options_from_task_data_var:awesome_options"]
            if isinstance(value, list):
                if len(value) == 1:
                    first_element_in_value_list = value[0]
                    if isinstance(first_element_in_value_list, str):
                        if first_element_in_value_list.startswith("options_from_task_data_var:"):
                            task_data_var = first_element_in_value_list.replace("options_from_task_data_var:", "")

                            if task_data_var not in task_data:
                                message = (
                                    "Error building form. Attempting to create a selection list with options from"
                                    f" variable '{task_data_var}' but it doesn't exist in the Task Data."
                                )
                                raise ApiError(
                                    error_code="missing_task_data_var",
                                    message=message,
                                    status_code=500,
                                )

                            select_options_from_task_data = task_data.get(task_data_var)
                            if select_options_from_task_data == []:
                                raise ApiError(
                                    error_code="invalid_form_data",
                                    message=(
                                        "This form depends on variables, but at least one variable was empty. The"
                                        f" variable '{task_data_var}' must be a list with at least one element."
                                    ),
                                    status_code=500,
                                )
                            if isinstance(select_options_from_task_data, str):
                                raise ApiError(
                                    error_code="invalid_form_data",
                                    message=(
                                        "This form depends on enum variables, but at least one variable was a string."
                                        f" The variable '{task_data_var}' must be a list with at least one element."
                                    ),
                                    status_code=500,
                                )
                            if isinstance(select_options_from_task_data, list):
                                if all("value" in d and "label" in d for d in select_options_from_task_data):

                                    def map_function(
                                        task_data_select_option: TaskDataSelectOption,
                                    ) -> ReactJsonSchemaSelectOption:
                                        return {
                                            "type": "string",
                                            "enum": [task_data_select_option["value"]],
                                            "title": task_data_select_option["label"],
                                        }

                                    options_for_react_json_schema_form = list(
                                        map(
                                            map_function,
                                            select_options_from_task_data,
                                        )
                                    )

                                    in_dict[k] = options_for_react_json_schema_form
                                else:
                                    in_dict[k] = select_options_from_task_data
        elif isinstance(value, dict):
            _update_form_schema_with_task_data_as_needed(value, task_data)
        elif isinstance(value, list):
            for o in value:
                if isinstance(o, dict):
                    _update_form_schema_with_task_data_as_needed(o, task_data)


def _munge_form_ui_schema_based_on_hidden_fields_in_task_data(form_ui_schema: dict | None, task_data: dict) -> None:
    if form_ui_schema is None:
        return
    if task_data and "form_ui_hidden_fields" in task_data:
        hidden_fields = task_data["form_ui_hidden_fields"]
        for hidden_field in hidden_fields:
            hidden_field_parts = hidden_field.split(".")
            relevant_depth_of_ui_schema = form_ui_schema
            for ii, hidden_field_part in enumerate(hidden_field_parts):
                if hidden_field_part not in relevant_depth_of_ui_schema:
                    relevant_depth_of_ui_schema[hidden_field_part] = {}
                relevant_depth_of_ui_schema = relevant_depth_of_ui_schema[hidden_field_part]
                if len(hidden_field_parts) == ii + 1:
                    relevant_depth_of_ui_schema["ui:widget"] = "hidden"
