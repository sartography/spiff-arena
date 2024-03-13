import json
import uuid
from typing import Any
from uuid import UUID

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
from spiffworkflow_backend.data_migrations.process_instance_migrator import ProcessInstanceMigrator
from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.exceptions.process_entity_not_found_error import ProcessEntityNotFoundError
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.human_task_user import HumanTaskUserModel
from spiffworkflow_backend.models.principal import PrincipalModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance_file_data import ProcessInstanceFileDataModel
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.models.reference_cache import ReferenceCacheModel
from spiffworkflow_backend.models.reference_cache import ReferenceSchema
from spiffworkflow_backend.models.task import TaskModel  # noqa: F401
from spiffworkflow_backend.services.authentication_service import AuthenticationService  # noqa: F401
from spiffworkflow_backend.services.authorization_service import AuthorizationService
from spiffworkflow_backend.services.git_service import GitCommandError
from spiffworkflow_backend.services.git_service import GitService
from spiffworkflow_backend.services.jinja_service import JinjaService
from spiffworkflow_backend.services.process_caller_service import ProcessCallerService
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.process_instance_queue_service import ProcessInstanceQueueService
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.task_service import TaskModelError
from spiffworkflow_backend.services.task_service import TaskService

process_api_blueprint = Blueprint("process_api", __name__)


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
        permission_base_uri="/v1.0/process-instances",
        process_model_identifiers=process_model_identifiers,
    )
    permitted_references = []
    for spec_reference in references:
        if spec_reference.relative_location in permitted_process_model_identifiers:
            permitted_references.append(spec_reference)
    return ReferenceSchema(many=True).dump(permitted_references)


def process_caller_list(bpmn_process_identifiers: list[str]) -> Any:
    callers = ProcessCallerService.callers(bpmn_process_identifiers)
    references = (
        ReferenceCacheModel.basic_query()
        .filter_by(type="process")
        .filter(ReferenceCacheModel.identifier.in_(callers))  # type: ignore
        .all()
    )
    return ReferenceSchema(many=True).dump(references)


def _process_data_fetcher(
    process_instance_id: int,
    process_data_identifier: str,
    category: str,
    bpmn_process_guid: str | None = None,
    process_identifier: str | None = None,
) -> flask.wrappers.Response:
    if process_identifier and bpmn_process_guid is None:
        raise ApiError(
            error_code="missing_required_parameter",
            message="process_identifier was given but bpmn_process_guid was not. Both must be provided if either is required.",
            status_code=404,
        )
    if process_identifier is None and bpmn_process_guid:
        raise ApiError(
            error_code="missing_required_parameter",
            message="bpmn_process_guid was given but process_identifier was not. Both must be provided if either is required.",
            status_code=404,
        )

    process_instance = _find_process_instance_by_id_or_raise(process_instance_id)
    processor = ProcessInstanceProcessor(process_instance)

    bpmn_process_instance = processor.bpmn_process_instance
    bpmn_process_data = processor.get_data()
    if process_identifier and bpmn_process_instance.spec.name != process_identifier:
        bpmn_process_instance = processor.bpmn_process_instance.subprocesses.get(UUID(bpmn_process_guid))
        if bpmn_process_instance is None:
            raise ApiError(
                error_code="bpmn_process_not_found",
                message=f"Cannot find a bpmn process with guid '{bpmn_process_guid}' for process instance {process_instance.id}",
                status_code=404,
            )
        bpmn_process_data = bpmn_process_instance.data

    data_objects = bpmn_process_instance.spec.data_objects
    data_object = data_objects.get(process_data_identifier)
    if data_object is None:
        raise ApiError(
            error_code="data_object_not_found",
            message=(
                f"Cannot find a data object with identifier '{process_data_identifier}' for bpmn process '{process_identifier}'"
                f" in process instance {process_instance.id}"
            ),
            status_code=404,
        )

    if hasattr(data_object, "category") and data_object.category is not None:
        if data_object.category != category:
            raise ApiError(
                error_code="data_object_category_mismatch",
                message=f"The desired data object has category '{data_object.category}' instead of the expected '{category}'",
                status_code=400,
            )

    process_data_value = bpmn_process_data.get(process_data_identifier)

    return make_response(
        jsonify(
            {
                "process_data_identifier": process_data_identifier,
                "process_data_value": process_data_value,
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
    file_contents = file_data.contents

    return Response(
        file_contents,
        mimetype=mimetype,
        headers={"Content-disposition": f"attachment; filename={filename}"},
    )


def _get_required_parameter_or_raise(parameter: str, post_body: dict[str, Any]) -> Any:
    return_value = None
    if parameter in post_body:
        return_value = post_body[parameter]

    if return_value is None or return_value == "":
        raise (
            ApiError(
                error_code="missing_required_parameter",
                message=f"Parameter is missing from json request body: {parameter}",
                status_code=400,
            )
        )

    return return_value


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
        target_uri = f"/v1.0/process-instances/for-me/{modified_process_model_identifier}/{process_instance.id}"
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

    # we're dequeing twice in this function.
    # tried to wrap the whole block in one dequeue, but that has the confusing side-effect that every exception
    # in the block causes the process instance to go into an error state. for example, when
    # AuthorizationService.assert_user_can_complete_task raises. this would have been solvable, but this seems simpler,
    # and the cost is not huge given that this function is not the most common code path in the world.
    with ProcessInstanceQueueService.dequeued(process_instance):
        ProcessInstanceMigrator.run(process_instance)

    processor = ProcessInstanceProcessor(
        process_instance, workflow_completed_handler=ProcessInstanceService.schedule_next_process_model_cycle
    )
    spiff_task = _get_spiff_task_from_processor(task_guid, processor)
    AuthorizationService.assert_user_can_complete_task(process_instance.id, str(spiff_task.id), principal.user)

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

    with sentry_sdk.start_span(op="task", description="complete_form_task"):
        with ProcessInstanceQueueService.dequeued(process_instance):
            ProcessInstanceService.complete_form_task(
                processor=processor,
                spiff_task=spiff_task,
                data=body,
                user=g.user,
                human_task=human_task,
                execution_mode=execution_mode,
            )

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
    if (
        # "allowGuest" in spiff_task_extensions
        # and spiff_task_extensions["allowGuest"] == "true"
        # and "guestConfirmation" in spiff_task_extensions
        "guestConfirmation" in spiff_task_extensions
        and spiff_task_extensions["guestConfirmation"]
    ):
        guest_confirmation = JinjaService.render_jinja_template(spiff_task.task_spec.extensions["guestConfirmation"], task_model)
        return {"guest_confirmation": guest_confirmation}

    if processor.next_task():
        task = ProcessInstanceService.spiff_task_to_api_task(processor, processor.next_task())
        task.process_model_uses_queued_execution = queue_enabled_for_process_model(process_instance)
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

    human_task: HumanTaskModel = human_task_query.first()
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
