import json
from collections import OrderedDict
from collections.abc import Generator
from typing import Any

import flask.wrappers
import sentry_sdk
from flask import current_app
from flask import g
from flask import jsonify
from flask import make_response
from flask import request
from flask import stream_with_context
from flask.wrappers import Response
from SpiffWorkflow.bpmn.exceptions import WorkflowTaskException  # type: ignore
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow  # type: ignore
from SpiffWorkflow.spiff.specs.defaults import ServiceTask  # type: ignore
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore
from SpiffWorkflow.util.task import TaskState  # type: ignore
from sqlalchemy import and_
from sqlalchemy import desc
from sqlalchemy import func
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import aliased
from sqlalchemy.orm.util import AliasedClass

from spiffworkflow_backend.background_processing.celery_tasks.process_instance_task_producer import (
    queue_enabled_for_process_model,
)
from spiffworkflow_backend.background_processing.celery_tasks.process_instance_task_producer import (
    queue_process_instance_if_appropriate,
)
from spiffworkflow_backend.constants import SPIFFWORKFLOW_BACKEND_SERIALIZER_VERSION
from spiffworkflow_backend.data_migrations.process_instance_migrator import ProcessInstanceMigrator
from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.exceptions.error import HumanTaskAlreadyCompletedError
from spiffworkflow_backend.helpers.spiff_enum import ProcessInstanceExecutionMode
from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.human_task_user import HumanTaskUserAddedBy
from spiffworkflow_backend.models.human_task_user import HumanTaskUserModel
from spiffworkflow_backend.models.json_data import JsonDataModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
from spiffworkflow_backend.models.process_instance import ProcessInstanceTaskDataCannotBeUpdatedError
from spiffworkflow_backend.models.process_instance_error_detail import ProcessInstanceErrorDetailModel
from spiffworkflow_backend.models.process_instance_event import ProcessInstanceEventModel
from spiffworkflow_backend.models.process_instance_event import ProcessInstanceEventType
from spiffworkflow_backend.models.task import Task
from spiffworkflow_backend.models.task import TaskModel
from spiffworkflow_backend.models.task_definition import TaskDefinitionModel
from spiffworkflow_backend.models.task_draft_data import TaskDraftDataDict
from spiffworkflow_backend.models.task_draft_data import TaskDraftDataModel
from spiffworkflow_backend.models.task_instructions_for_end_user import TaskInstructionsForEndUserModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.routes.process_api_blueprint import _find_principal_or_raise
from spiffworkflow_backend.routes.process_api_blueprint import _find_process_instance_by_id_or_raise
from spiffworkflow_backend.routes.process_api_blueprint import _find_process_instance_for_me_or_raise
from spiffworkflow_backend.routes.process_api_blueprint import _get_process_model
from spiffworkflow_backend.routes.process_api_blueprint import _get_spiff_task_from_processor
from spiffworkflow_backend.routes.process_api_blueprint import _get_task_model_for_request
from spiffworkflow_backend.routes.process_api_blueprint import _get_task_model_from_guid_or_raise
from spiffworkflow_backend.routes.process_api_blueprint import _munge_form_ui_schema_based_on_hidden_fields_in_task_data
from spiffworkflow_backend.routes.process_api_blueprint import _task_submit_shared
from spiffworkflow_backend.routes.process_api_blueprint import _update_form_schema_with_task_data_as_needed
from spiffworkflow_backend.services.authorization_service import AuthorizationService
from spiffworkflow_backend.services.error_handling_service import ErrorHandlingService
from spiffworkflow_backend.services.jinja_service import JinjaService
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.process_instance_queue_service import ProcessInstanceIsAlreadyLockedError
from spiffworkflow_backend.services.process_instance_queue_service import ProcessInstanceQueueService
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService
from spiffworkflow_backend.services.process_instance_tmp_service import ProcessInstanceTmpService
from spiffworkflow_backend.services.task_service import TaskService


def task_allows_guest(
    process_instance_id: int,
    task_guid: str,
) -> flask.wrappers.Response:
    allows_guest = False
    if process_instance_id and task_guid and TaskModel.task_guid_allows_guest(task_guid, process_instance_id):
        allows_guest = True
    return make_response(jsonify({"allows_guest": allows_guest}), 200)


# this is currently not used by the Frontend
def task_list_my_tasks(process_instance_id: int | None = None, page: int = 1, per_page: int = 100) -> flask.wrappers.Response:
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
        .join(
            HumanTaskUserModel,
            HumanTaskUserModel.human_task_id == HumanTaskModel.id,
        )
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
        HumanTaskModel.created_at_in_seconds,
        HumanTaskModel.updated_at_in_seconds,
        HumanTaskModel.json_metadata,
        func.max(ProcessInstanceModel.process_model_identifier).label("process_model_identifier"),
        func.max(ProcessInstanceModel.status).label("process_instance_status"),
        func.max(ProcessInstanceModel.summary).label("process_instance_summary"),
        func.max(ProcessInstanceModel.last_milestone_bpmn_name).label("last_milestone_bpmn_name"),
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


def task_list_completed_by_me(process_instance_id: int, page: int = 1, per_page: int = 100) -> flask.wrappers.Response:
    user_id = g.user.id

    human_tasks_query = db.session.query(HumanTaskModel).filter(
        HumanTaskModel.completed == True,  # noqa: E712
        HumanTaskModel.completed_by_user_id == user_id,
        HumanTaskModel.process_instance_id == process_instance_id,
    )

    human_tasks = human_tasks_query.order_by(desc(HumanTaskModel.id)).paginate(  # type: ignore
        page=page, per_page=per_page, error_out=False
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


def task_list_completed(process_instance_id: int, page: int = 1, per_page: int = 100) -> flask.wrappers.Response:
    human_tasks_query = (
        db.session.query(HumanTaskModel)  # type: ignore
        .join(UserModel, UserModel.id == HumanTaskModel.completed_by_user_id)
        .filter(
            HumanTaskModel.completed == True,  # noqa: E712
            HumanTaskModel.process_instance_id == process_instance_id,
        )
        .add_columns(
            HumanTaskModel.task_name,
            HumanTaskModel.task_title,
            HumanTaskModel.process_model_display_name,
            HumanTaskModel.process_instance_id,
            HumanTaskModel.updated_at_in_seconds,
            HumanTaskModel.created_at_in_seconds,
            HumanTaskModel.json_metadata,
            UserModel.username.label("completed_by_username"),  # type: ignore
        )
    )

    human_tasks = human_tasks_query.order_by(desc(HumanTaskModel.id)).paginate(  # type: ignore
        page=page, per_page=per_page, error_out=False
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


def task_list_for_my_open_processes(page: int = 1, per_page: int = 100) -> flask.wrappers.Response:
    return _get_tasks(page=page, per_page=per_page)


def service_task_list_awaiting_callback(page: int = 1, per_page: int = 100) -> flask.wrappers.Response:
    user_id = g.user.id
    task_models = (
        db.session.query(TaskModel)  # type: ignore
        .join(TaskDefinitionModel)
        .join(ProcessInstanceModel)
        .filter(
            TaskModel.state == "STARTED",
            TaskDefinitionModel.typename == "ServiceTask",
            ProcessInstanceModel.process_initiator_id == user_id,
            ProcessInstanceModel.status == "waiting",
        )
        .add_columns(
            TaskModel.guid,
            TaskModel.state,
            TaskModel.process_instance_id,
            TaskDefinitionModel.bpmn_name.label("task_name"),  # type: ignore
            TaskDefinitionModel.bpmn_identifier,
            TaskDefinitionModel.typename,
            ProcessInstanceModel.status.label("process_instance_status"),  # type: ignore
            ProcessInstanceModel.process_model_identifier,
            ProcessInstanceModel.process_model_display_name,
        )
        .order_by(
            desc(TaskModel.process_instance_id)  # type: ignore
        )
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    results = []
    for row in task_models.items:
        results.append(
            {
                "id": row.guid,
                "name": row.bpmn_identifier,
                "title": row.task_name or row.bpmn_identifier,
                "type": row.typename,
                "state": row.state,
                "process_instance_id": row.process_instance_id,
                "process_instance_status": row.process_instance_status,
                "process_model_identifier": row.process_model_identifier,
                "process_model_display_name": row.process_model_display_name,
            }
        )

    response_json = {
        "results": results,
        "pagination": {
            "count": len(task_models.items),
            "total": task_models.total,
            "pages": task_models.pages,
        },
    }

    return make_response(jsonify(response_json), 200)


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
                f"The process instance needs to be suspended to update the task-data. It is currently: {process_instance.status}"
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
            json_data_dict = TaskService.update_json_data_on_db_model_and_return_dict_if_updated(
                task_model, new_task_data_dict, "json_data_hash"
            )
            if json_data_dict is not None:
                JsonDataModel.insert_or_update_json_data_records({json_data_dict["hash"]: json_data_dict})
                ProcessInstanceTmpService.add_event_to_process_instance(
                    process_instance,
                    ProcessInstanceEventType.task_data_edited.value,
                    task_guid=task_guid,
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
        json.dumps(process_instance.serialized()),
        status=200,
        mimetype="application/json",
    )


def task_instance_list(
    process_instance_id: int,
    task_guid: str,
) -> Response:
    task_model = _get_task_model_from_guid_or_raise(task_guid, process_instance_id)
    task_model_instances = (
        TaskModel.query.filter_by(task_definition_id=task_model.task_definition.id, bpmn_process_id=task_model.bpmn_process_id)
        .join(TaskDefinitionModel, TaskDefinitionModel.id == TaskModel.task_definition_id)
        .add_columns(
            TaskDefinitionModel.bpmn_identifier,
            TaskDefinitionModel.bpmn_name,
            TaskDefinitionModel.typename,
            TaskDefinitionModel.properties_json.label("task_definition_properties_json"),  # type: ignore
            TaskModel.guid,
            TaskModel.state,
            TaskModel.end_in_seconds,
            TaskModel.start_in_seconds,
            TaskModel.runtime_info,
            TaskModel.properties_json,
        )
    ).all()

    sorted_task_models = TaskModel.sort_by_last_state_changed(task_model_instances)
    return make_response(jsonify(sorted_task_models), 200)


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
        with ProcessInstanceQueueService.dequeued(process_instance):
            ProcessInstanceMigrator.run(process_instance)
            processor = ProcessInstanceProcessor(process_instance)
            processor.manual_complete_task(task_guid, execute, g.user)
    else:
        raise ApiError(
            error_code="complete_task",
            message=f"Could not complete Task {task_guid} in Instance {process_instance_id}",
        )
    return Response(
        json.dumps(process_instance.serialized()),
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
    human_tasks = HumanTaskModel.query.filter_by(process_instance_id=process_instance.id, task_id=task_model.guid).all()

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
            human_task_user = HumanTaskUserModel(
                user_id=user_id, human_task=human_task, added_by=HumanTaskUserAddedBy.manual.value
            )
            db.session.add(human_task_user)

    SpiffworkflowBaseDBModel.commit_with_rollback_on_exception()

    return make_response(jsonify({"ok": True}), 200)


def prepare_form(body: dict) -> flask.wrappers.Response:
    """Does the backend processing of the form schema as it would be done for task_show, including
    running the form schema through a jinja rendering, hiding fields, and populating lists of options."""

    if "form_schema" not in body:
        raise ApiError(
            "missing_form_schema",
            "The form schema is missing from the request body.",
        )

    form_schema = body["form_schema"]
    form_ui = body.get("form_ui", {})
    task_data = body.get("task_data", {})

    # Run the form schema through the jinja template engine
    form_string = json.dumps(form_schema)
    form_string = JinjaService.render_jinja_template(form_string, task_data=task_data)
    form_dict = OrderedDict(json.loads(form_string))
    # Update the schema if it, for instance, uses task data to populate an options list.
    _update_form_schema_with_task_data_as_needed(form_dict, task_data)

    # Hide any fields that are marked as hidden in the task data.
    _munge_form_ui_schema_based_on_hidden_fields_in_task_data(form_ui, task_data)

    return make_response(jsonify({"form_schema": form_dict, "form_ui": form_ui}), 200)


def task_show(
    process_instance_id: int,
    task_guid: str = "next",
    with_form_data: bool = False,
) -> flask.wrappers.Response:
    task_model = _get_task_model_for_request(
        process_instance_id=process_instance_id,
        task_guid=task_guid,
        with_form_data=with_form_data,
    )
    return make_response(jsonify(task_model), 200)


def task_submit(
    process_instance_id: int,
    task_guid: str,
    body: dict[str, Any] | None = None,
    execution_mode: str | None = None,
) -> flask.wrappers.Response:
    with sentry_sdk.start_span(op="controller_action", name="tasks_controller.task_submit"):
        if body is None:
            body = {}
        response_item = _task_submit_shared(process_instance_id, task_guid, body, execution_mode=execution_mode)
        if "next_task_assigned_to_me" in response_item:
            response_item = response_item["next_task_assigned_to_me"]
        elif "next_task" in response_item:
            response_item = response_item["next_task"]
        return make_response(jsonify(response_item), 200)


def _complete_service_task_that_is_waiting_for_callback(
    process_instance_id: int,
    task_guid: str,
    execution_mode: str | None = None,
) -> dict:
    """Complete a service task that is waiting for a callback after returning 202.

    This is called when a long-running service task returns a 202 (Accepted) response,
    leaving the task in STARTED state. The connector later calls back with the result.
    """

    if not request.is_json:
        raise ApiError(
            error_code="invalid_mimetype",
            message="This endpoint must be called with a json mimetype.",
            status_code=400,
        )

    process_instance = _find_process_instance_by_id_or_raise(process_instance_id)
    error = None

    with sentry_sdk.start_span(op="task", name="complete_service_task_callback"):
        with ProcessInstanceQueueService.dequeued(process_instance, max_attempts=3):
            if ProcessInstanceMigrator.run(process_instance):
                # Refresh the process instance to get any updates from migration
                db.session.refresh(process_instance)

            processor = ProcessInstanceProcessor(
                process_instance, workflow_completed_handler=ProcessInstanceService.schedule_next_process_model_cycle
            )
            spiff_task = _get_spiff_task_from_processor(task_guid, processor)

            # assure we are waiting for a callback.
            if spiff_task.state == TaskState.STARTED and isinstance(spiff_task.task_spec, ServiceTask):
                queue_process_instance_if_appropriate(process_instance, execution_mode)

                # Set the result variable with the parsed response, just like CustomServiceTask._execute does
                result_variable = spiff_task.task_spec.result_variable
                content = request.json
                if content is None:
                    content = {}
                if "body" in content:
                    content = content["body"]
                if result_variable:
                    spiff_task.data[result_variable] = content

                user = UserModel.query.filter_by(id=g.user.id).first()
                processor.complete_task(spiff_task, user)

                # Run the engine steps.
                execution_strategy_name = None
                if execution_mode == ProcessInstanceExecutionMode.synchronous.value:
                    execution_strategy_name = "greedy"
                processor.do_engine_steps(save=True, execution_strategy_name=execution_strategy_name)
            else:
                error = ApiError(
                    error_code="not_waiting_for_callback",
                    message="This process instance is not waiting for a callback.",
                    status_code=400,
                )
        if error:
            raise error  # Raise the error outside the process intance queue service, so we don't error out the process.

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


def service_task_submit_callback(
    process_instance_id: int,
    task_guid: str,
    execution_mode: str | None = None,
) -> flask.wrappers.Response:
    with sentry_sdk.start_span(op="controller_action", name="tasks_controller.service_task_submit_callback"):
        response_item = _complete_service_task_that_is_waiting_for_callback(process_instance_id, task_guid, execution_mode)
        if "next_task" in response_item:
            response_item = response_item["next_task"]
        return make_response(jsonify(response_item), 200)


def process_instance_progress(
    process_instance_id: int,
) -> flask.wrappers.Response:
    response: dict[str, Task | ProcessInstanceModel | list | dict[str, str]] = {}
    process_instance = _find_process_instance_for_me_or_raise(process_instance_id, include_actions=True)

    principal = _find_principal_or_raise()
    next_human_task_assigned_to_me = TaskService.next_human_task_for_user(process_instance_id, principal.user_id)
    if next_human_task_assigned_to_me:
        response["task"] = HumanTaskModel.to_task(next_human_task_assigned_to_me)
    # this may not catch all times we should redirect to instance show page
    elif not process_instance.is_immediately_runnable() or ProcessInstanceTmpService.is_enqueued_to_run_in_the_future(
        process_instance
    ):
        # any time we assign this process_instance, the frontend progress page will redirect to process instance show
        response["process_instance"] = process_instance

        # look for the most recent error event for this instance
        if process_instance.status in [ProcessInstanceStatus.error.value, ProcessInstanceStatus.suspended.value]:
            pi_error_details = (
                ProcessInstanceErrorDetailModel.query.join(
                    ProcessInstanceEventModel,
                    ProcessInstanceErrorDetailModel.process_instance_event_id == ProcessInstanceEventModel.id,
                )
                .filter(
                    ProcessInstanceEventModel.process_instance_id == process_instance.id,
                    ProcessInstanceEventModel.event_type.in_(  # type: ignore
                        [
                            ProcessInstanceEventType.process_instance_error.value,
                            ProcessInstanceEventType.task_failed.value,
                        ]
                    ),
                )
                .order_by(ProcessInstanceEventModel.timestamp.desc())  # type: ignore
                .first()
            )
            if pi_error_details is not None:
                response["error_details"] = pi_error_details
                task_model = pi_error_details.process_instance_event.task()
                if task_model is not None:
                    response["process_instance_event"] = {
                        "task_definition_identifier": task_model.task_definition.bpmn_identifier,
                        "task_definition_name": task_model.task_definition.bpmn_name,
                    }

    user_instructions = TaskInstructionsForEndUserModel.retrieve_and_clear(process_instance.id)
    response["instructions"] = user_instructions

    return make_response(jsonify(response), 200)


def task_with_instruction(process_instance_id: int) -> Response:
    process_instance = _find_process_instance_by_id_or_raise(process_instance_id)
    processor = ProcessInstanceProcessor(process_instance, include_task_data_for_completed_tasks=True)
    spiff_task = processor.next_task()
    task = None
    if spiff_task is not None:
        task = ProcessInstanceService.spiff_task_to_api_task(processor, spiff_task)
        try:
            instructions = _render_instructions(spiff_task)
        except Exception as exception:
            raise ApiError(
                error_code="engine_steps_error",
                message=f"Failed to complete an automated task. Error was: {str(exception)}",
                status_code=400,
            ) from exception
        task.properties = {"instructionsForEndUser": instructions}
    return make_response(jsonify({"task": task}), 200)


def _render_instructions(spiff_task: SpiffTask, task_data: dict | None = None) -> str:
    return JinjaService.render_instructions_for_end_user(spiff_task, task_data=task_data)


def _interstitial_stream(
    process_instance: ProcessInstanceModel,
    execute_tasks: bool = True,
    is_locked: bool = False,
) -> Generator[str, str | None, None]:
    def get_reportable_tasks(processor: ProcessInstanceProcessor) -> Any:
        return processor.bpmn_process_instance.get_tasks(
            state=TaskState.WAITING | TaskState.STARTED | TaskState.READY | TaskState.ERROR
        )

    # do not attempt to get task instructions if process instance is suspended or was terminated
    if process_instance.status in ["suspended", "terminated"]:
        yield _render_data("unrunnable_instance", process_instance)
        return

    processor = ProcessInstanceProcessor(process_instance)
    reported_ids = []  # A list of all the ids reported by this endpoint so far.
    tasks = get_reportable_tasks(processor)
    while True:
        has_ready_tasks = False
        for spiff_task in tasks:
            # ignore the instructions if they are on the EndEvent for the top level process
            if not TaskService.is_main_process_end_event(spiff_task):
                try:
                    instructions = _render_instructions(spiff_task)
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
                has_ready_tasks = True

        if has_ready_tasks:
            # do not do any processing if the instance is not currently active
            if process_instance.status not in ProcessInstanceModel.active_statuses():
                yield _render_data("unrunnable_instance", process_instance)
                return
            if execute_tasks:
                try:
                    # run_until_user_message does not run tasks with instructions so run readys first
                    # to force it to run the task.
                    processor.do_engine_steps(execution_strategy_name="run_current_ready_tasks")
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
            if is_locked and process_instance.status not in [
                "not_started",
                "waiting",
            ]:
                break

        tasks = get_reportable_tasks(processor)

    spiff_task = processor.next_task()
    if spiff_task is not None and spiff_task.id not in reported_ids:
        task_data = spiff_task.data
        if task_data is None or task_data == {}:
            json_data = (
                JsonDataModel.query.join(TaskModel, TaskModel.json_data_hash == JsonDataModel.hash)
                .filter(TaskModel.guid == str(spiff_task.id))
                .first()
            )
            if json_data is not None:
                task_data = json_data.data
        task = ProcessInstanceService.spiff_task_to_api_task(processor, spiff_task)
        try:
            instructions = _render_instructions(spiff_task, task_data=task_data)
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
    return len([t for t in bpmn_process_instance.get_tasks(state=TaskState.READY) if not t.task_spec.manual])


def _dequeued_interstitial_stream(
    process_instance_id: int, execute_tasks: bool = True
) -> Generator[str | None, str | None, None]:
    try:
        process_instance = _find_process_instance_by_id_or_raise(process_instance_id)

        # TODO: currently this just redirects back to home if the process has not been started
        # need something better to show?
        if execute_tasks:
            try:
                if not ProcessInstanceTmpService.is_enqueued_to_run_in_the_future(process_instance):
                    with ProcessInstanceQueueService.dequeued(process_instance):
                        ProcessInstanceMigrator.run(process_instance)
                        yield from _interstitial_stream(process_instance, execute_tasks=execute_tasks)
            except ProcessInstanceIsAlreadyLockedError:
                yield from _interstitial_stream(process_instance, execute_tasks=False, is_locked=True)
        else:
            # attempt to run the migrator even for a readonly operation if the process instance is not newest
            if (
                process_instance.spiff_serializer_version is not None
                and process_instance.spiff_serializer_version < SPIFFWORKFLOW_BACKEND_SERIALIZER_VERSION
            ):
                try:
                    with ProcessInstanceQueueService.dequeued(process_instance):
                        ProcessInstanceMigrator.run(process_instance)
                except ProcessInstanceIsAlreadyLockedError:
                    pass
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
        AuthorizationService.assert_user_can_complete_human_task(process_instance.id, task_guid, principal.user)
    except HumanTaskAlreadyCompletedError:
        return make_response(jsonify({"ok": True}), 200)

    task_model = _get_task_model_from_guid_or_raise(task_guid, process_instance_id)
    full_bpmn_process_id_path = TaskService.full_bpmn_process_path(task_model.bpmn_process, "id")
    task_definition_id_path = f"{':'.join(map(str, full_bpmn_process_id_path))}:{task_model.task_definition_id}"
    task_draft_data_dict: TaskDraftDataDict = {
        "process_instance_id": process_instance.id,
        "task_definition_id_path": task_definition_id_path,
        "saved_form_data_hash": None,
    }

    json_data_dict = JsonDataModel.json_data_dict_from_dict(body)
    JsonDataModel.insert_or_update_json_data_dict(json_data_dict)
    task_draft_data_dict["saved_form_data_hash"] = json_data_dict["hash"]
    try:
        TaskDraftDataModel.insert_or_update_task_draft_data_dict(task_draft_data_dict)
        db.session.commit()
    except OperationalError as exception:
        db.session.rollback()
        if "Deadlock" in str(exception):
            task_draft_data = TaskService.task_draft_data_from_task_model(task_model)
            # if we do not find a task_draft_data record, that means it was deleted when the form was submitted
            # and we therefore have no need to save draft data
            if task_draft_data is not None:
                # using this method here since it will check the db if the json_data_hash
                # has changed and then we can update the task_data_draft record if it has
                new_json_data_dict = TaskService.update_json_data_on_db_model_and_return_dict_if_updated(
                    task_draft_data, body, "saved_form_data_hash"
                )
                if new_json_data_dict is not None:
                    JsonDataModel.insert_or_update_json_data_dict(new_json_data_dict)
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
                human_tasks_query = human_tasks_query.filter(HumanTaskModel.lane_assignment_id.is_not(None))  # type: ignore
        else:
            human_tasks_query = human_tasks_query.filter(HumanTaskModel.lane_assignment_id.is_(None))  # type: ignore

    potential_owner_usernames_from_group_concat_or_similar = _get_potential_owner_usernames(assigned_user)

    process_model_identifier_column = ProcessInstanceModel.process_model_identifier
    process_instance_status_column = ProcessInstanceModel.status.label("process_instance_status")  # type: ignore
    user_username_column = UserModel.username.label("process_initiator_username")  # type: ignore
    group_identifier_column = GroupModel.identifier.label("assigned_user_group_identifier")  # type: ignore
    lane_name_column = HumanTaskModel.lane_name
    if current_app.config["SPIFFWORKFLOW_BACKEND_DATABASE_TYPE"] == "postgres":
        process_model_identifier_column = func.max(ProcessInstanceModel.process_model_identifier).label(
            "process_model_identifier"
        )
        process_instance_status_column = func.max(ProcessInstanceModel.status).label("process_instance_status")
        user_username_column = func.max(UserModel.username).label("process_initiator_username")
        group_identifier_column = func.max(GroupModel.identifier).label("assigned_user_group_identifier")
        lane_name_column = func.max(HumanTaskModel.lane_name).label("lane_name")

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
            HumanTaskModel.json_metadata,
            lane_name_column,
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


def _get_potential_owner_usernames(assigned_user: AliasedClass) -> Any:
    potential_owner_usernames_from_group_concat_or_similar = func.group_concat(assigned_user.username.distinct()).label(
        "potential_owner_usernames"
    )
    db_type = current_app.config.get("SPIFFWORKFLOW_BACKEND_DATABASE_TYPE")

    if db_type == "postgres":
        potential_owner_usernames_from_group_concat_or_similar = func.string_agg(assigned_user.username.distinct(), ", ").label(
            "potential_owner_usernames"
        )

    return potential_owner_usernames_from_group_concat_or_similar
