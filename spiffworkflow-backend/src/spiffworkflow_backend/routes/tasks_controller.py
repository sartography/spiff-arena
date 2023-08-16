import json
import os
import uuid
from collections.abc import Generator
from typing import Any
from typing import TypedDict

import flask.wrappers
import sentry_sdk
from flask import current_app
from flask import g
from flask import jsonify
from flask import make_response
from flask import stream_with_context
from flask.wrappers import Response
from MySQLdb import OperationalError  # type: ignore
from SpiffWorkflow.bpmn.exceptions import WorkflowTaskException  # type: ignore
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow  # type: ignore
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore
from SpiffWorkflow.task import TaskState
from sqlalchemy import and_
from sqlalchemy import asc
from sqlalchemy import desc
from sqlalchemy import func
from sqlalchemy.orm import aliased
from sqlalchemy.orm.util import AliasedClass

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.human_task_user import HumanTaskUserModel
from spiffworkflow_backend.models.json_data import JsonDataModel  # noqa: F401
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModelSchema
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
from spiffworkflow_backend.models.process_instance import ProcessInstanceTaskDataCannotBeUpdatedError
from spiffworkflow_backend.models.process_instance_event import ProcessInstanceEventType
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.models.task import Task
from spiffworkflow_backend.models.task import TaskModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.routes.process_api_blueprint import _find_principal_or_raise
from spiffworkflow_backend.routes.process_api_blueprint import _find_process_instance_by_id_or_raise
from spiffworkflow_backend.routes.process_api_blueprint import _get_process_model
from spiffworkflow_backend.services.authorization_service import AuthorizationService
from spiffworkflow_backend.services.authorization_service import HumanTaskAlreadyCompletedError
from spiffworkflow_backend.services.authorization_service import HumanTaskNotFoundError
from spiffworkflow_backend.services.authorization_service import UserDoesNotHaveAccessToTaskError
from spiffworkflow_backend.services.error_handling_service import ErrorHandlingService
from spiffworkflow_backend.services.file_system_service import FileSystemService
from spiffworkflow_backend.services.jinja_service import JinjaService
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.process_instance_queue_service import ProcessInstanceIsAlreadyLockedError
from spiffworkflow_backend.services.process_instance_queue_service import ProcessInstanceQueueService
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService
from spiffworkflow_backend.services.process_instance_tmp_service import ProcessInstanceTmpService
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.spec_file_service import SpecFileService
from spiffworkflow_backend.services.task_service import TaskModelError
from spiffworkflow_backend.services.task_service import TaskService


class TaskDataSelectOption(TypedDict):
    value: str
    label: str


class ReactJsonSchemaSelectOption(TypedDict):
    type: str
    title: str
    enum: list[str]


# this is currently not used by the Frontend
def task_list_my_tasks(
    process_instance_id: int | None = None, page: int = 1, per_page: int = 100
) -> flask.wrappers.Response:
    principal = _find_principal_or_raise()
    assigned_user = aliased(UserModel)
    process_initiator_user = aliased(UserModel)
    human_task_query = (
        HumanTaskModel.query.order_by(desc(HumanTaskModel.id))  # type: ignore
        .group_by(HumanTaskModel.id)
        .join(
            ProcessInstanceModel,
            ProcessInstanceModel.id == HumanTaskModel.process_instance_id,
        )
        .join(
            process_initiator_user,
            process_initiator_user.id == ProcessInstanceModel.process_initiator_id,
        )
        .join(HumanTaskUserModel, HumanTaskUserModel.human_task_id == HumanTaskModel.id)
        .filter(HumanTaskUserModel.user_id == principal.user_id)
        .outerjoin(assigned_user, assigned_user.id == HumanTaskUserModel.user_id)
        .filter(HumanTaskModel.completed == False)  # noqa: E712
        .outerjoin(GroupModel, GroupModel.id == HumanTaskModel.lane_assignment_id)
    )

    if process_instance_id is not None:
        human_task_query = human_task_query.filter(
            ProcessInstanceModel.id == process_instance_id,
            ProcessInstanceModel.status != ProcessInstanceStatus.error.value,
        )

    potential_owner_usernames_from_group_concat_or_similar = _get_potential_owner_usernames(assigned_user)

    # FIXME: this breaks postgres. Look at commit c147cdb47b1481f094b8c3d82dc502fe961f4977 for
    # UPDATE: maybe fixed in postgres and mysql. remove comment if so.
    # the postgres fix but it breaks the method for mysql.
    # error in postgres:
    #   psycopg2.errors.GroupingError) column \"process_instance.process_model_identifier\" must
    #   appear in the GROUP BY clause or be used in an aggregate function
    human_tasks = human_task_query.add_columns(
        HumanTaskModel.task_id.label("id"),  # type: ignore
        HumanTaskModel.task_name,
        HumanTaskModel.task_title,
        HumanTaskModel.process_model_display_name,
        HumanTaskModel.process_instance_id,
        func.max(ProcessInstanceModel.process_model_identifier).label("process_model_identifier"),
        func.max(ProcessInstanceModel.status).label("process_instance_status"),
        func.max(ProcessInstanceModel.updated_at_in_seconds).label("updated_at_in_seconds"),
        func.max(ProcessInstanceModel.created_at_in_seconds).label("created_at_in_seconds"),
        func.max(process_initiator_user.username).label("process_initiator_username"),
        func.max(GroupModel.identifier).label("assigned_user_group_identifier"),
        potential_owner_usernames_from_group_concat_or_similar,
    ).paginate(page=page, per_page=per_page, error_out=False)

    response_json = {
        "results": human_tasks.items,
        "pagination": {
            "count": len(human_tasks.items),
            "total": human_tasks.total,
            "pages": human_tasks.pages,
        },
    }

    return make_response(jsonify(response_json), 200)


def task_list_for_my_open_processes(page: int = 1, per_page: int = 100) -> flask.wrappers.Response:
    return _get_tasks(page=page, per_page=per_page)


def task_list_for_me(page: int = 1, per_page: int = 100) -> flask.wrappers.Response:
    return _get_tasks(
        processes_started_by_user=False,
        has_lane_assignment_id=False,
        page=page,
        per_page=per_page,
    )


def task_list_for_my_groups(
    user_group_identifier: str | None = None, page: int = 1, per_page: int = 100
) -> flask.wrappers.Response:
    return _get_tasks(
        user_group_identifier=user_group_identifier,
        processes_started_by_user=False,
        page=page,
        per_page=per_page,
    )


def task_data_show(
    modified_process_model_identifier: str,
    process_instance_id: int,
    task_guid: str,
) -> flask.wrappers.Response:
    task_model = _get_task_model_from_guid_or_raise(task_guid, process_instance_id)
    task_model.data = task_model.json_data()
    return make_response(jsonify(task_model), 200)


def task_data_update(
    process_instance_id: int,
    modified_process_model_identifier: str,
    task_guid: str,
    body: dict,
) -> Response:
    process_instance = ProcessInstanceModel.query.filter(ProcessInstanceModel.id == process_instance_id).first()
    if process_instance:
        if process_instance.status != "suspended":
            raise ProcessInstanceTaskDataCannotBeUpdatedError(
                "The process instance needs to be suspended to update the task-data."
                f" It is currently: {process_instance.status}"
            )

        task_model = TaskModel.query.filter_by(guid=task_guid).first()
        if task_model is None:
            raise ApiError(
                error_code="update_task_data_error",
                message=f"Could not find Task: {task_guid} in Instance: {process_instance_id}.",
            )

        if "new_task_data" in body:
            new_task_data_str: str = body["new_task_data"]
            new_task_data_dict = json.loads(new_task_data_str)
            json_data_dict = TaskService.update_task_data_on_task_model_and_return_dict_if_updated(
                task_model, new_task_data_dict, "json_data_hash"
            )
            if json_data_dict is not None:
                JsonDataModel.insert_or_update_json_data_records({json_data_dict["hash"]: json_data_dict})
                ProcessInstanceTmpService.add_event_to_process_instance(
                    process_instance, ProcessInstanceEventType.task_data_edited.value, task_guid=task_guid
                )
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                raise ApiError(
                    error_code="update_task_data_error",
                    message=f"Could not update the Instance. Original error is {e}",
                ) from e
    else:
        raise ApiError(
            error_code="update_task_data_error",
            message=f"Could not update task data for Instance: {process_instance_id}, and Task: {task_guid}.",
        )
    return Response(
        json.dumps(ProcessInstanceModelSchema().dump(process_instance)),
        status=200,
        mimetype="application/json",
    )


def manual_complete_task(
    modified_process_model_identifier: str,
    process_instance_id: int,
    task_guid: str,
    body: dict,
) -> Response:
    """Mark a task complete without executing it."""
    execute = body.get("execute", True)
    process_instance = ProcessInstanceModel.query.filter(ProcessInstanceModel.id == process_instance_id).first()
    if process_instance:
        processor = ProcessInstanceProcessor(process_instance)
        processor.manual_complete_task(task_guid, execute, g.user)
    else:
        raise ApiError(
            error_code="complete_task",
            message=f"Could not complete Task {task_guid} in Instance {process_instance_id}",
        )
    return Response(
        json.dumps(ProcessInstanceModelSchema().dump(process_instance)),
        status=200,
        mimetype="application/json",
    )


def task_assign(
    modified_process_model_identifier: str,
    process_instance_id: int,
    task_guid: str,
    body: dict,
) -> Response:
    process_instance = _find_process_instance_by_id_or_raise(process_instance_id)

    if process_instance.status != ProcessInstanceStatus.suspended.value:
        raise ApiError(
            error_code="error_not_suspended",
            message="The process instance must be suspended to perform this operation",
            status_code=400,
        )

    if "user_ids" not in body:
        raise ApiError(
            error_code="malformed_request",
            message="user_ids as an array must be given in the body of the request.",
            status_code=400,
        )

    _get_process_model(
        process_instance.process_model_identifier,
    )

    task_model = _get_task_model_from_guid_or_raise(task_guid, process_instance_id)
    human_tasks = HumanTaskModel.query.filter_by(
        process_instance_id=process_instance.id, task_id=task_model.guid
    ).all()

    if len(human_tasks) > 1:
        raise ApiError(
            error_code="multiple_tasks_found",
            message="More than one ready tasks were found. This should never happen.",
            status_code=400,
        )

    human_task = human_tasks[0]

    for user_id in body["user_ids"]:
        human_task_user = HumanTaskUserModel.query.filter_by(user_id=user_id, human_task=human_task).first()
        if human_task_user is None:
            human_task_user = HumanTaskUserModel(user_id=user_id, human_task=human_task)
            db.session.add(human_task_user)

    SpiffworkflowBaseDBModel.commit_with_rollback_on_exception()

    return make_response(jsonify({"ok": True}), 200)


def task_show(
    process_instance_id: int, task_guid: str = "next", with_form_data: bool = False
) -> flask.wrappers.Response:
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
        AuthorizationService.assert_user_can_complete_task(process_instance.id, task_model.guid, g.user)
        can_complete = True
    except (HumanTaskNotFoundError, UserDoesNotHaveAccessToTaskError, HumanTaskAlreadyCompletedError):
        can_complete = False

    task_model.process_model_display_name = process_model.display_name
    task_model.process_model_identifier = process_model.id
    task_model.typename = task_definition.typename
    task_model.can_complete = can_complete
    task_model.name_for_display = TaskService.get_name_for_display(task_definition)

    if with_form_data:
        task_process_identifier = task_model.bpmn_process.bpmn_process_definition.bpmn_identifier
        process_model_with_form = process_model

        refs = SpecFileService.get_references_for_process(process_model_with_form)
        all_processes = [i.identifier for i in refs]
        if task_process_identifier not in all_processes:
            top_bpmn_process = TaskService.bpmn_process_for_called_activity_or_top_level_process(task_model)
            bpmn_file_full_path = ProcessInstanceProcessor.bpmn_file_full_path_from_bpmn_process_identifier(
                top_bpmn_process.bpmn_process_definition.bpmn_identifier
            )
            relative_path = os.path.relpath(bpmn_file_full_path, start=FileSystemService.root_path())
            process_model_relative_path = os.path.dirname(relative_path)
            process_model_with_form = ProcessModelService.get_process_model_from_relative_path(
                process_model_relative_path
            )

        form_schema_file_name = ""
        form_ui_schema_file_name = ""
        extensions = TaskService.get_extensions_from_task_model(task_model)
        task_model.signal_buttons = TaskService.get_ready_signals_with_button_labels(
            process_instance_id, task_model.guid
        )

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
                        message=(
                            f"Cannot find a form file for process_instance_id: {process_instance_id}, task_guid:"
                            f" {task_guid}"
                        ),
                        status_code=400,
                    )
                )

            form_dict = _prepare_form_data(
                form_schema_file_name,
                task_model,
                process_model_with_form,
            )

            if task_model.data:
                _update_form_schema_with_task_data_as_needed(form_dict, task_model)

            if form_dict:
                task_model.form_schema = form_dict

            if form_ui_schema_file_name:
                ui_form_contents = _prepare_form_data(
                    form_ui_schema_file_name,
                    task_model,
                    process_model_with_form,
                )
                if ui_form_contents:
                    task_model.form_ui_schema = ui_form_contents

            _munge_form_ui_schema_based_on_hidden_fields_in_task_data(task_model)
        JinjaService.render_instructions_for_end_user(task_model, extensions)
        task_model.extensions = extensions

    return make_response(jsonify(task_model), 200)


def task_submit(
    process_instance_id: int,
    task_guid: str,
    body: dict[str, Any],
) -> flask.wrappers.Response:
    with sentry_sdk.start_span(op="controller_action", description="tasks_controller.task_submit"):
        return _task_submit_shared(process_instance_id, task_guid, body)


def _interstitial_stream(
    process_instance: ProcessInstanceModel, execute_tasks: bool = True, is_locked: bool = False
) -> Generator[str, str | None, None]:
    def get_reportable_tasks() -> Any:
        return processor.bpmn_process_instance.get_tasks(
            TaskState.WAITING | TaskState.STARTED | TaskState.READY | TaskState.ERROR
        )

    def render_instructions(spiff_task: SpiffTask) -> str:
        task_model = TaskModel.query.filter_by(guid=str(spiff_task.id)).first()
        if task_model is None:
            return ""
        return JinjaService.render_instructions_for_end_user(task_model)

    # do not attempt to get task instructions if process instance is suspended or was terminated
    if process_instance.status in ["suspended", "terminated"]:
        yield _render_data("unrunnable_instance", process_instance)
        return

    processor = ProcessInstanceProcessor(process_instance)
    reported_ids = []  # A list of all the ids reported by this endpoint so far.
    tasks = get_reportable_tasks()
    while True:
        for spiff_task in tasks:
            # ignore the instructions if they are on the EndEvent for the top level process
            if not TaskService.is_main_process_end_event(spiff_task):
                try:
                    instructions = render_instructions(spiff_task)
                except Exception as e:
                    api_error = ApiError(
                        error_code="engine_steps_error",
                        message=f"Failed to complete an automated task. Error was: {str(e)}",
                        status_code=400,
                    )
                    yield _render_data("error", api_error)
                    raise e
                if instructions and spiff_task.id not in reported_ids:
                    task = ProcessInstanceService.spiff_task_to_api_task(processor, spiff_task)
                    task.properties = {"instructionsForEndUser": instructions}
                    yield _render_data("task", task)
                    reported_ids.append(spiff_task.id)
            if spiff_task.state == TaskState.READY:
                # do not do any processing if the instance is not currently active
                if process_instance.status not in ProcessInstanceModel.active_statuses():
                    yield _render_data("unrunnable_instance", process_instance)
                    return
                if execute_tasks:
                    try:
                        # run_until_user_message does not run tasks with instructions to use one_at_a_time
                        # to force it to run the task.
                        processor.do_engine_steps(execution_strategy_name="one_at_a_time")
                        processor.do_engine_steps(execution_strategy_name="run_until_user_message")
                        processor.save()  # Fixme - maybe find a way not to do this on every loop?
                        processor.refresh_waiting_tasks()

                    except WorkflowTaskException as wfe:
                        api_error = ApiError.from_workflow_exception(
                            "engine_steps_error", "Failed to complete an automated task.", exp=wfe
                        )
                        yield _render_data("error", api_error)
                        ErrorHandlingService.handle_error(process_instance, wfe)
                        return
                # return if process instance is now complete and let the frontend redirect to show page
                if process_instance.status not in ProcessInstanceModel.active_statuses():
                    yield _render_data("unrunnable_instance", process_instance)
                    return

        # path used by the interstitial page while executing tasks - ie the background processor is not executing them
        ready_engine_task_count = _get_ready_engine_step_count(processor.bpmn_process_instance)
        if execute_tasks and ready_engine_task_count == 0:
            break

        if not execute_tasks:
            # path used by the process instance show page to display most recent instructions
            if not is_locked:
                break

            # HACK: db.session.refresh doesn't seem to refresh without rollback or commit so use rollback.
            # we are not executing tasks so there shouldn't be anything to write anyway, so no harm in rollback.
            # https://stackoverflow.com/a/20361132/6090676
            # note that the thing changing the data in this case is probably the background worker,
            # and it is definitely committing its changes, but since we have already queried the data,
            # our session has stale results without the rollback.
            db.session.rollback()
            db.session.refresh(process_instance)
            processor = ProcessInstanceProcessor(process_instance)

            # if process instance is done or blocked by a human task, then break out
            if is_locked and process_instance.status not in ["not_started", "waiting"]:
                break

        tasks = get_reportable_tasks()

    spiff_task = processor.next_task()
    if spiff_task is not None:
        task = ProcessInstanceService.spiff_task_to_api_task(processor, spiff_task)
        if task.id not in reported_ids:
            try:
                instructions = render_instructions(spiff_task)
            except Exception as e:
                api_error = ApiError(
                    error_code="engine_steps_error",
                    message=f"Failed to complete an automated task. Error was: {str(e)}",
                    status_code=400,
                )
                yield _render_data("error", api_error)
                raise e
            task.properties = {"instructionsForEndUser": instructions}
            yield _render_data("task", task)


def _get_ready_engine_step_count(bpmn_process_instance: BpmnWorkflow) -> int:
    return len([t for t in bpmn_process_instance.get_tasks(TaskState.READY) if not t.task_spec.manual])


def _dequeued_interstitial_stream(
    process_instance_id: int, execute_tasks: bool = True
) -> Generator[str | None, str | None, None]:
    try:
        process_instance = _find_process_instance_by_id_or_raise(process_instance_id)

        # TODO: currently this just redirects back to home if the process has not been started
        # need something better to show?
        if execute_tasks:
            try:
                if not ProcessInstanceQueueService.is_enqueued_to_run_in_the_future(process_instance):
                    with ProcessInstanceQueueService.dequeued(process_instance):
                        yield from _interstitial_stream(process_instance, execute_tasks=execute_tasks)
            except ProcessInstanceIsAlreadyLockedError:
                yield from _interstitial_stream(process_instance, execute_tasks=False, is_locked=True)
        else:
            # no reason to get a lock if we are reading only
            yield from _interstitial_stream(process_instance, execute_tasks=execute_tasks)
    except Exception as ex:
        # the stream_with_context method seems to swallow exceptions so also attempt to catch errors here
        api_error = ApiError(
            error_code="interstitial_error",
            message=(
                f"Received error trying to run process instance: {process_instance_id}. "
                f"Error was: {ex.__class__.__name__}: {str(ex)}"
            ),
            status_code=500,
        )
        yield _render_data("error", api_error)


def interstitial(process_instance_id: int, execute_tasks: bool = True) -> Response:
    """A Server Side Events Stream for watching the execution of engine tasks."""
    try:
        return Response(
            stream_with_context(_dequeued_interstitial_stream(process_instance_id, execute_tasks=execute_tasks)),
            mimetype="text/event-stream",
            headers={"X-Accel-Buffering": "no"},
        )
    except Exception as ex:
        api_error = ApiError(
            error_code="interstitial_error",
            message=(
                f"Received error trying to run process instance: {process_instance_id}. "
                f"Error was: {ex.__class__.__name__}: {str(ex)}"
            ),
            status_code=500,
            response_headers={"Content-type": "text/event-stream"},
        )
        api_error.response_message = _render_data("error", api_error)
        raise api_error from ex


def _render_data(return_type: str, entity: ApiError | Task | ProcessInstanceModel) -> str:
    return_hash: dict = {"type": return_type}
    return_hash[return_type] = entity
    return f"data: {current_app.json.dumps(return_hash)} \n\n"


def task_save_draft(
    process_instance_id: int,
    task_guid: str,
    body: dict[str, Any],
) -> flask.wrappers.Response:
    principal = _find_principal_or_raise()
    process_instance = _find_process_instance_by_id_or_raise(process_instance_id)
    if not process_instance.can_submit_task():
        return Response(
            json.dumps(
                {
                    "ok": True,
                    "saved": False,
                    "message": (
                        f"Process Instance ({process_instance.id}) has status "
                        f"{process_instance.status} which does not allow draft data to be saved."
                    ),
                    "process_model_identifier": process_instance.process_model_identifier,
                    "process_instance_id": process_instance_id,
                }
            ),
            status=200,
            mimetype="application/json",
        )

    try:
        AuthorizationService.assert_user_can_complete_task(process_instance.id, task_guid, principal.user)
    except HumanTaskAlreadyCompletedError:
        return make_response(jsonify({"ok": True}), 200)

    task_model = _get_task_model_from_guid_or_raise(task_guid, process_instance_id)
    task_draft_data = TaskService.task_draft_data_from_task_model(task_model, create_if_not_exists=True)

    if task_draft_data is not None:
        json_data_dict = TaskService.update_task_data_on_task_model_and_return_dict_if_updated(
            task_draft_data, body, "saved_form_data_hash"
        )
        if json_data_dict is not None:
            JsonDataModel.insert_or_update_json_data_dict(json_data_dict)
            db.session.add(task_draft_data)
            try:
                db.session.commit()
            except OperationalError as exception:
                db.session.rollback()
                if "Deadlock" in str(exception):
                    task_draft_data = TaskService.task_draft_data_from_task_model(task_model)
                    # if we do not find a task_draft_data record, that means it was deleted when the form was submitted
                    # and we therefore have no need to save draft data
                    if task_draft_data is not None:
                        json_data_dict = TaskService.update_task_data_on_task_model_and_return_dict_if_updated(
                            task_draft_data, body, "saved_form_data_hash"
                        )
                        if json_data_dict is not None:
                            JsonDataModel.insert_or_update_json_data_dict(json_data_dict)
                            db.session.add(task_draft_data)
                            db.session.commit()
                else:
                    raise exception

    return Response(
        json.dumps(
            {
                "ok": True,
                "saved": True,
                "process_model_identifier": process_instance.process_model_identifier,
                "process_instance_id": process_instance_id,
            }
        ),
        status=200,
        mimetype="application/json",
    )


def _task_submit_shared(
    process_instance_id: int,
    task_guid: str,
    body: dict[str, Any],
) -> flask.wrappers.Response:
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

    processor = ProcessInstanceProcessor(process_instance)
    spiff_task = _get_spiff_task_from_process_instance(task_guid, process_instance, processor=processor)
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
            )

    # delete draft data when we submit a task to ensure cycling back to the task contains the
    # most up-to-date data
    task_draft_data = TaskService.task_draft_data_from_task_model(human_task.task_model)
    if task_draft_data is not None:
        db.session.delete(task_draft_data)
        db.session.commit()

    next_human_task_assigned_to_me = (
        HumanTaskModel.query.filter_by(process_instance_id=process_instance_id, completed=False)
        .order_by(asc(HumanTaskModel.id))  # type: ignore
        .join(HumanTaskUserModel)
        .filter_by(user_id=principal.user_id)
        .first()
    )
    if next_human_task_assigned_to_me:
        return make_response(jsonify(HumanTaskModel.to_task(next_human_task_assigned_to_me)), 200)
    elif processor.next_task():
        task = ProcessInstanceService.spiff_task_to_api_task(processor, processor.next_task())
        return make_response(jsonify(task), 200)

    return Response(
        json.dumps(
            {
                "ok": True,
                "process_model_identifier": process_instance.process_model_identifier,
                "process_instance_id": process_instance_id,
            }
        ),
        status=202,
        mimetype="application/json",
    )


def _get_tasks(
    processes_started_by_user: bool = True,
    has_lane_assignment_id: bool = True,
    page: int = 1,
    per_page: int = 100,
    user_group_identifier: str | None = None,
) -> flask.wrappers.Response:
    user_id = g.user.id

    # use distinct to ensure we only get one row per human task otherwise
    # we can get back multiple for the same human task row which throws off
    # pagination later on
    # https://stackoverflow.com/q/34582014/6090676
    human_tasks_query = (
        db.session.query(HumanTaskModel)
        .group_by(HumanTaskModel.id)  # type: ignore
        .outerjoin(GroupModel, GroupModel.id == HumanTaskModel.lane_assignment_id)
        .join(ProcessInstanceModel)
        .join(UserModel, UserModel.id == ProcessInstanceModel.process_initiator_id)
        .filter(
            HumanTaskModel.completed == False,  # noqa: E712
            ProcessInstanceModel.status != ProcessInstanceStatus.error.value,
        )
    )

    assigned_user = aliased(UserModel)
    if processes_started_by_user:
        human_tasks_query = (
            human_tasks_query.filter(ProcessInstanceModel.process_initiator_id == user_id)
            .outerjoin(
                HumanTaskUserModel,
                HumanTaskModel.id == HumanTaskUserModel.human_task_id,
            )
            .outerjoin(assigned_user, assigned_user.id == HumanTaskUserModel.user_id)
        )
    else:
        human_tasks_query = human_tasks_query.filter(ProcessInstanceModel.process_initiator_id != user_id).join(
            HumanTaskUserModel,
            and_(
                HumanTaskUserModel.user_id == user_id,
                HumanTaskModel.id == HumanTaskUserModel.human_task_id,
            ),
        )

        if has_lane_assignment_id:
            if user_group_identifier:
                human_tasks_query = human_tasks_query.filter(GroupModel.identifier == user_group_identifier)
            else:
                human_tasks_query = human_tasks_query.filter(
                    HumanTaskModel.lane_assignment_id.is_not(None)  # type: ignore
                )
        else:
            human_tasks_query = human_tasks_query.filter(HumanTaskModel.lane_assignment_id.is_(None))  # type: ignore

    potential_owner_usernames_from_group_concat_or_similar = _get_potential_owner_usernames(assigned_user)

    process_model_identifier_column = ProcessInstanceModel.process_model_identifier
    process_instance_status_column = ProcessInstanceModel.status.label("process_instance_status")  # type: ignore
    user_username_column = UserModel.username.label("process_initiator_username")  # type: ignore
    group_identifier_column = GroupModel.identifier.label("assigned_user_group_identifier")
    if current_app.config["SPIFFWORKFLOW_BACKEND_DATABASE_TYPE"] == "postgres":
        process_model_identifier_column = func.max(ProcessInstanceModel.process_model_identifier).label(
            "process_model_identifier"
        )
        process_instance_status_column = func.max(ProcessInstanceModel.status).label("process_instance_status")
        user_username_column = func.max(UserModel.username).label("process_initiator_username")
        group_identifier_column = func.max(GroupModel.identifier).label("assigned_user_group_identifier")

    human_tasks = (
        human_tasks_query.add_columns(
            process_model_identifier_column,
            process_instance_status_column,
            user_username_column,
            group_identifier_column,
            HumanTaskModel.task_name,
            HumanTaskModel.task_title,
            HumanTaskModel.process_model_display_name,
            HumanTaskModel.process_instance_id,
            HumanTaskModel.updated_at_in_seconds,
            HumanTaskModel.created_at_in_seconds,
            potential_owner_usernames_from_group_concat_or_similar,
        )
        .order_by(desc(HumanTaskModel.id))  # type: ignore
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    response_json = {
        "results": human_tasks.items,
        "pagination": {
            "count": len(human_tasks.items),
            "total": human_tasks.total,
            "pages": human_tasks.pages,
        },
    }

    return make_response(jsonify(response_json), 200)


def _prepare_form_data(form_file: str, task_model: TaskModel, process_model: ProcessModelInfo) -> dict:
    if task_model.data is None:
        return {}

    file_contents = SpecFileService.get_data(process_model, form_file).decode("utf-8")
    try:
        form_contents = JinjaService.render_jinja_template(file_contents, task_model)
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
    except TaskModelError as wfe:
        wfe.add_note(f"Error in Json Form File '{form_file}'")
        api_error = ApiError.from_workflow_exception("instructions_error", str(wfe), exp=wfe)
        api_error.file_name = form_file
        raise api_error


def _get_spiff_task_from_process_instance(
    task_guid: str,
    process_instance: ProcessInstanceModel,
    processor: ProcessInstanceProcessor | None = None,
) -> SpiffTask:
    if processor is None:
        processor = ProcessInstanceProcessor(process_instance)
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


# originally from: https://bitcoden.com/answers/python-nested-dictionary-update-value-where-any-nested-key-matches
def _update_form_schema_with_task_data_as_needed(in_dict: dict, task_model: TaskModel) -> None:
    if task_model.data is None:
        return None

    for k, value in in_dict.items():
        if "anyOf" == k:
            # value will look like the array on the right of "anyOf": ["options_from_task_data_var:awesome_options"]
            if isinstance(value, list):
                if len(value) == 1:
                    first_element_in_value_list = value[0]
                    if isinstance(first_element_in_value_list, str):
                        if first_element_in_value_list.startswith("options_from_task_data_var:"):
                            task_data_var = first_element_in_value_list.replace("options_from_task_data_var:", "")

                            if task_data_var not in task_model.data:
                                message = (
                                    "Error building form. Attempting to create a selection list with options from"
                                    f" variable '{task_data_var}' but it doesn't exist in the Task Data."
                                )
                                raise ApiError(
                                    error_code="missing_task_data_var",
                                    message=message,
                                    status_code=500,
                                )

                            select_options_from_task_data = task_model.data.get(task_data_var)
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
                                        map(map_function, select_options_from_task_data)
                                    )

                                    in_dict[k] = options_for_react_json_schema_form
        elif isinstance(value, dict):
            _update_form_schema_with_task_data_as_needed(value, task_model)
        elif isinstance(value, list):
            for o in value:
                if isinstance(o, dict):
                    _update_form_schema_with_task_data_as_needed(o, task_model)


def _get_potential_owner_usernames(assigned_user: AliasedClass) -> Any:
    potential_owner_usernames_from_group_concat_or_similar = func.group_concat(
        assigned_user.username.distinct()
    ).label("potential_owner_usernames")
    db_type = current_app.config.get("SPIFFWORKFLOW_BACKEND_DATABASE_TYPE")

    if db_type == "postgres":
        potential_owner_usernames_from_group_concat_or_similar = func.string_agg(
            assigned_user.username.distinct(), ", "
        ).label("potential_owner_usernames")

    return potential_owner_usernames_from_group_concat_or_similar


def _find_human_task_or_raise(
    process_instance_id: int,
    task_guid: str,
    only_tasks_that_can_be_completed: bool = False,
) -> HumanTaskModel:
    if only_tasks_that_can_be_completed:
        human_task_query = HumanTaskModel.query.filter_by(
            process_instance_id=process_instance_id, task_id=task_guid, completed=False
        )
    else:
        human_task_query = HumanTaskModel.query.filter_by(process_instance_id=process_instance_id, task_id=task_guid)

    human_task: HumanTaskModel = human_task_query.first()
    if human_task is None:
        raise (
            ApiError(
                error_code="no_human_task",
                message=(
                    f"Cannot find a task to complete for task id '{task_guid}' and"
                    f" process instance {process_instance_id}."
                ),
                status_code=500,
            )
        )
    return human_task


def _munge_form_ui_schema_based_on_hidden_fields_in_task_data(task_model: TaskModel) -> None:
    if task_model.form_ui_schema is None:
        task_model.form_ui_schema = {}

    if task_model.data and "form_ui_hidden_fields" in task_model.data:
        hidden_fields = task_model.data["form_ui_hidden_fields"]
        for hidden_field in hidden_fields:
            hidden_field_parts = hidden_field.split(".")
            relevant_depth_of_ui_schema = task_model.form_ui_schema
            for ii, hidden_field_part in enumerate(hidden_field_parts):
                if hidden_field_part not in relevant_depth_of_ui_schema:
                    relevant_depth_of_ui_schema[hidden_field_part] = {}
                relevant_depth_of_ui_schema = relevant_depth_of_ui_schema[hidden_field_part]
                if len(hidden_field_parts) == ii + 1:
                    relevant_depth_of_ui_schema["ui:widget"] = "hidden"


def _get_task_model_from_guid_or_raise(task_guid: str, process_instance_id: int) -> TaskModel:
    task_model: TaskModel | None = TaskModel.query.filter_by(
        guid=task_guid, process_instance_id=process_instance_id
    ).first()
    if task_model is None:
        raise ApiError(
            error_code="task_not_found",
            message=f"Cannot find a task with guid '{task_guid}' for process instance '{process_instance_id}'",
            status_code=400,
        )
    return task_model
