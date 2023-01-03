"""APIs for dealing with process groups, process models, and process instances."""
import json
import os
import uuid
from typing import Any
from typing import Dict
from typing import Optional
from typing import TypedDict
from typing import Union

import flask.wrappers
import jinja2
from flask import g
from flask import jsonify
from flask import make_response
from flask.wrappers import Response
from flask_bpmn.api.api_error import ApiError
from flask_bpmn.models.db import db
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore
from SpiffWorkflow.task import TaskState
from sqlalchemy import and_
from sqlalchemy import asc
from sqlalchemy import desc
from sqlalchemy import func
from sqlalchemy.orm import aliased

from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.human_task_user import HumanTaskUserModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.routes.process_api_blueprint import (
    _find_principal_or_raise,
)
from spiffworkflow_backend.routes.process_api_blueprint import (
    _find_process_instance_by_id_or_raise,
)
from spiffworkflow_backend.routes.process_api_blueprint import _get_process_model
from spiffworkflow_backend.services.authorization_service import AuthorizationService
from spiffworkflow_backend.services.file_system_service import FileSystemService
from spiffworkflow_backend.services.process_instance_processor import (
    ProcessInstanceProcessor,
)
from spiffworkflow_backend.services.process_instance_service import (
    ProcessInstanceService,
)
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.spec_file_service import SpecFileService


class TaskDataSelectOption(TypedDict):
    """TaskDataSelectOption."""

    value: str
    label: str


class ReactJsonSchemaSelectOption(TypedDict):
    """ReactJsonSchemaSelectOption."""

    type: str
    title: str
    enum: list[str]


# TODO: see comment for before_request
# @process_api_blueprint.route("/v1.0/tasks", methods=["GET"])
def task_list_my_tasks(page: int = 1, per_page: int = 100) -> flask.wrappers.Response:
    """Task_list_my_tasks."""
    principal = _find_principal_or_raise()
    human_tasks = (
        HumanTaskModel.query.order_by(desc(HumanTaskModel.id))  # type: ignore
        .join(ProcessInstanceModel)
        .join(HumanTaskUserModel)
        .filter_by(user_id=principal.user_id)
        .filter(HumanTaskModel.completed == False)  # noqa: E712
        # just need this add_columns to add the process_model_identifier. Then add everything back that was removed.
        .add_columns(
            ProcessInstanceModel.process_model_identifier,
            ProcessInstanceModel.process_model_display_name,
            ProcessInstanceModel.status,
            HumanTaskModel.task_name,
            HumanTaskModel.task_title,
            HumanTaskModel.task_type,
            HumanTaskModel.task_status,
            HumanTaskModel.task_id,
            HumanTaskModel.id,
            HumanTaskModel.process_model_display_name,
            HumanTaskModel.process_instance_id,
        )
        .paginate(page=page, per_page=per_page, error_out=False)
    )
    tasks = [HumanTaskModel.to_task(human_task) for human_task in human_tasks.items]

    response_json = {
        "results": tasks,
        "pagination": {
            "count": len(human_tasks.items),
            "total": human_tasks.total,
            "pages": human_tasks.pages,
        },
    }

    return make_response(jsonify(response_json), 200)


def task_list_for_my_open_processes(
    page: int = 1, per_page: int = 100
) -> flask.wrappers.Response:
    """Task_list_for_my_open_processes."""
    return _get_tasks(page=page, per_page=per_page)


def task_list_for_me(page: int = 1, per_page: int = 100) -> flask.wrappers.Response:
    """Task_list_for_me."""
    return _get_tasks(
        processes_started_by_user=False,
        has_lane_assignment_id=False,
        page=page,
        per_page=per_page,
    )


def task_list_for_my_groups(
    user_group_identifier: Optional[str] = None, page: int = 1, per_page: int = 100
) -> flask.wrappers.Response:
    """Task_list_for_my_groups."""
    return _get_tasks(
        user_group_identifier=user_group_identifier,
        processes_started_by_user=False,
        page=page,
        per_page=per_page,
    )


def task_show(process_instance_id: int, task_id: str) -> flask.wrappers.Response:
    """Task_show."""
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

    human_task = HumanTaskModel.query.filter_by(
        process_instance_id=process_instance_id, task_id=task_id
    ).first()
    if human_task is None:
        raise (
            ApiError(
                error_code="no_human_task",
                message=f"Cannot find a task to complete for task id '{task_id}' and process instance {process_instance_id}.",
                status_code=500,
            )
        )

    form_schema_file_name = ""
    form_ui_schema_file_name = ""
    spiff_task = _get_spiff_task_from_process_instance(task_id, process_instance)
    extensions = spiff_task.task_spec.extensions

    if "properties" in extensions:
        properties = extensions["properties"]
        if "formJsonSchemaFilename" in properties:
            form_schema_file_name = properties["formJsonSchemaFilename"]
        if "formUiSchemaFilename" in properties:
            form_ui_schema_file_name = properties["formUiSchemaFilename"]
    processor = ProcessInstanceProcessor(process_instance)
    task = ProcessInstanceService.spiff_task_to_api_task(processor, spiff_task)
    task.data = spiff_task.data
    task.process_model_display_name = process_model.display_name
    task.process_model_identifier = process_model.id

    process_model_with_form = process_model
    refs = SpecFileService.get_references_for_process(process_model_with_form)
    all_processes = [i.identifier for i in refs]
    if task.process_identifier not in all_processes:
        bpmn_file_full_path = (
            ProcessInstanceProcessor.bpmn_file_full_path_from_bpmn_process_identifier(
                task.process_identifier
            )
        )
        relative_path = os.path.relpath(
            bpmn_file_full_path, start=FileSystemService.root_path()
        )
        process_model_relative_path = os.path.dirname(relative_path)
        process_model_with_form = (
            ProcessModelService.get_process_model_from_relative_path(
                process_model_relative_path
            )
        )

    if task.type == "User Task":
        if not form_schema_file_name:
            raise (
                ApiError(
                    error_code="missing_form_file",
                    message=f"Cannot find a form file for process_instance_id: {process_instance_id}, task_id: {task_id}",
                    status_code=400,
                )
            )

        form_contents = _prepare_form_data(
            form_schema_file_name,
            task.data,
            process_model_with_form,
        )

        try:
            # form_contents is a str
            form_dict = json.loads(form_contents)
        except Exception as exception:
            raise (
                ApiError(
                    error_code="error_loading_form",
                    message=f"Could not load form schema from: {form_schema_file_name}. Error was: {str(exception)}",
                    status_code=400,
                )
            ) from exception

        if task.data:
            _update_form_schema_with_task_data_as_needed(form_dict, task.data)

        if form_contents:
            task.form_schema = form_dict

        if form_ui_schema_file_name:
            ui_form_contents = _prepare_form_data(
                form_ui_schema_file_name,
                task.data,
                process_model_with_form,
            )
            if ui_form_contents:
                task.form_ui_schema = ui_form_contents

    if task.properties and task.data and "instructionsForEndUser" in task.properties:
        if task.properties["instructionsForEndUser"]:
            task.properties["instructionsForEndUser"] = _render_jinja_template(
                task.properties["instructionsForEndUser"], task.data
            )
    return make_response(jsonify(task), 200)


def process_data_show(
    process_instance_id: int,
    process_data_identifier: str,
    modified_process_model_identifier: str,
) -> flask.wrappers.Response:
    """Process_data_show."""
    process_instance = _find_process_instance_by_id_or_raise(process_instance_id)
    processor = ProcessInstanceProcessor(process_instance)
    all_process_data = processor.get_data()
    process_data_value = None
    if process_data_identifier in all_process_data:
        process_data_value = all_process_data[process_data_identifier]

    return make_response(
        jsonify(
            {
                "process_data_identifier": process_data_identifier,
                "process_data_value": process_data_value,
            }
        ),
        200,
    )


def task_submit(
    process_instance_id: int,
    task_id: str,
    body: Dict[str, Any],
    terminate_loop: bool = False,
) -> flask.wrappers.Response:
    """Task_submit_user_data."""
    principal = _find_principal_or_raise()
    process_instance = _find_process_instance_by_id_or_raise(process_instance_id)
    if not process_instance.can_submit_task():
        raise ApiError(
            error_code="process_instance_not_runnable",
            message=f"Process Instance ({process_instance.id}) has status "
            f"{process_instance.status} which does not allow tasks to be submitted.",
            status_code=400,
        )

    processor = ProcessInstanceProcessor(process_instance)
    spiff_task = _get_spiff_task_from_process_instance(
        task_id, process_instance, processor=processor
    )
    AuthorizationService.assert_user_can_complete_spiff_task(
        process_instance.id, spiff_task, principal.user
    )

    if spiff_task.state != TaskState.READY:
        raise (
            ApiError(
                error_code="invalid_state",
                message="You may not update a task unless it is in the READY state.",
                status_code=400,
            )
        )

    if terminate_loop and spiff_task.is_looping():
        spiff_task.terminate_loop()

    human_task = HumanTaskModel.query.filter_by(
        process_instance_id=process_instance_id, task_id=task_id, completed=False
    ).first()
    if human_task is None:
        raise (
            ApiError(
                error_code="no_human_task",
                message=f"Cannot find a task to complete for task id '{task_id}' and process instance {process_instance_id}.",
                status_code=500,
            )
        )

    ProcessInstanceService.complete_form_task(
        processor=processor,
        spiff_task=spiff_task,
        data=body,
        user=g.user,
        human_task=human_task,
    )

    # If we need to update all tasks, then get the next ready task and if it a multi-instance with the same
    # task spec, complete that form as well.
    # if update_all:
    #     last_index = spiff_task.task_info()["mi_index"]
    #     next_task = processor.next_task()
    #     while next_task and next_task.task_info()["mi_index"] > last_index:
    #         __update_task(processor, next_task, form_data, user)
    #         last_index = next_task.task_info()["mi_index"]
    #         next_task = processor.next_task()

    next_human_task_assigned_to_me = (
        HumanTaskModel.query.filter_by(
            process_instance_id=process_instance_id, completed=False
        )
        .order_by(asc(HumanTaskModel.id))  # type: ignore
        .join(HumanTaskUserModel)
        .filter_by(user_id=principal.user_id)
        .first()
    )
    if next_human_task_assigned_to_me:
        return make_response(
            jsonify(HumanTaskModel.to_task(next_human_task_assigned_to_me)), 200
        )

    return Response(json.dumps({"ok": True}), status=202, mimetype="application/json")


def _get_tasks(
    processes_started_by_user: bool = True,
    has_lane_assignment_id: bool = True,
    page: int = 1,
    per_page: int = 100,
    user_group_identifier: Optional[str] = None,
) -> flask.wrappers.Response:
    """Get_tasks."""
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
        .filter(HumanTaskModel.completed == False)  # noqa: E712
    )

    assigned_user = aliased(UserModel)
    if processes_started_by_user:
        human_tasks_query = (
            human_tasks_query.filter(
                ProcessInstanceModel.process_initiator_id == user_id
            )
            .outerjoin(
                HumanTaskUserModel,
                HumanTaskModel.id == HumanTaskUserModel.human_task_id,
            )
            .outerjoin(assigned_user, assigned_user.id == HumanTaskUserModel.user_id)
        )
    else:
        human_tasks_query = human_tasks_query.filter(
            ProcessInstanceModel.process_initiator_id != user_id
        ).join(
            HumanTaskUserModel,
            and_(
                HumanTaskUserModel.user_id == user_id,
                HumanTaskModel.id == HumanTaskUserModel.human_task_id,
            ),
        )
        if has_lane_assignment_id:
            if user_group_identifier:
                human_tasks_query = human_tasks_query.filter(
                    GroupModel.identifier == user_group_identifier
                )
            else:
                human_tasks_query = human_tasks_query.filter(
                    HumanTaskModel.lane_assignment_id.is_not(None)  # type: ignore
                )
        else:
            human_tasks_query = human_tasks_query.filter(HumanTaskModel.lane_assignment_id.is_(None))  # type: ignore

    human_tasks = (
        human_tasks_query.add_columns(
            ProcessInstanceModel.process_model_identifier,
            ProcessInstanceModel.status.label("process_instance_status"),  # type: ignore
            ProcessInstanceModel.updated_at_in_seconds,
            ProcessInstanceModel.created_at_in_seconds,
            UserModel.username.label("process_initiator_username"),
            GroupModel.identifier.label("assigned_user_group_identifier"),
            HumanTaskModel.task_name,
            HumanTaskModel.task_title,
            HumanTaskModel.process_model_display_name,
            HumanTaskModel.process_instance_id,
            func.group_concat(assigned_user.username.distinct()).label(
                "potential_owner_usernames"
            ),
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


def _prepare_form_data(
    form_file: str, task_data: Union[dict, None], process_model: ProcessModelInfo
) -> str:
    """Prepare_form_data."""
    if task_data is None:
        return ""

    file_contents = SpecFileService.get_data(process_model, form_file).decode("utf-8")
    return _render_jinja_template(file_contents, task_data)


def _render_jinja_template(unprocessed_template: str, data: dict[str, Any]) -> str:
    """Render_jinja_template."""
    jinja_environment = jinja2.Environment(
        autoescape=True, lstrip_blocks=True, trim_blocks=True
    )
    template = jinja_environment.from_string(unprocessed_template)
    return template.render(**data)


def _get_spiff_task_from_process_instance(
    task_id: str,
    process_instance: ProcessInstanceModel,
    processor: Union[ProcessInstanceProcessor, None] = None,
) -> SpiffTask:
    """Get_spiff_task_from_process_instance."""
    if processor is None:
        processor = ProcessInstanceProcessor(process_instance)
    task_uuid = uuid.UUID(task_id)
    spiff_task = processor.bpmn_process_instance.get_task(task_uuid)

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
def _update_form_schema_with_task_data_as_needed(
    in_dict: dict, task_data: dict
) -> None:
    """Update_nested."""
    for k, value in in_dict.items():
        if "anyOf" == k:
            # value will look like the array on the right of "anyOf": ["options_from_task_data_var:awesome_options"]
            if isinstance(value, list):
                if len(value) == 1:
                    first_element_in_value_list = value[0]
                    if isinstance(first_element_in_value_list, str):
                        if first_element_in_value_list.startswith(
                            "options_from_task_data_var:"
                        ):
                            task_data_var = first_element_in_value_list.replace(
                                "options_from_task_data_var:", ""
                            )

                            if task_data_var not in task_data:
                                raise (
                                    ApiError(
                                        error_code="missing_task_data_var",
                                        message=f"Task data is missing variable: {task_data_var}",
                                        status_code=500,
                                    )
                                )

                            select_options_from_task_data = task_data.get(task_data_var)
                            if isinstance(select_options_from_task_data, list):
                                if all(
                                    "value" in d and "label" in d
                                    for d in select_options_from_task_data
                                ):

                                    def map_function(
                                        task_data_select_option: TaskDataSelectOption,
                                    ) -> ReactJsonSchemaSelectOption:
                                        """Map_function."""
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
            _update_form_schema_with_task_data_as_needed(value, task_data)
        elif isinstance(value, list):
            for o in value:
                if isinstance(o, dict):
                    _update_form_schema_with_task_data_as_needed(o, task_data)
