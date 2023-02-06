"""APIs for dealing with process groups, process models, and process instances."""
import json
import os
import uuid
from sys import exc_info
from typing import Any
from typing import Dict
from typing import Optional
from typing import TypedDict
from typing import Union

import flask.wrappers
import jinja2
import sentry_sdk
from flask import current_app
from flask import g
from flask import jsonify
from flask import make_response
from flask.wrappers import Response
from jinja2 import TemplateSyntaxError
from SpiffWorkflow.exceptions import WorkflowTaskException  # type: ignore
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore
from SpiffWorkflow.task import TaskState
from sqlalchemy import and_
from sqlalchemy import asc
from sqlalchemy import desc
from sqlalchemy import func
from sqlalchemy.orm import aliased
from sqlalchemy.orm.util import AliasedClass

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.human_task_user import HumanTaskUserModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.models.task import Task
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
def task_list_my_tasks(
    process_instance_id: Optional[int] = None, page: int = 1, per_page: int = 100
) -> flask.wrappers.Response:
    """Task_list_my_tasks."""
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
            ProcessInstanceModel.id == process_instance_id
        )

    potential_owner_usernames_from_group_concat_or_similar = (
        _get_potential_owner_usernames(assigned_user)
    )

    human_tasks = human_task_query.add_columns(
        HumanTaskModel.task_id.label("id"),  # type: ignore
        HumanTaskModel.task_name,
        HumanTaskModel.task_title,
        HumanTaskModel.process_model_display_name,
        HumanTaskModel.process_instance_id,
        ProcessInstanceModel.process_model_identifier,
        ProcessInstanceModel.status.label("process_instance_status"),  # type: ignore
        ProcessInstanceModel.updated_at_in_seconds,
        ProcessInstanceModel.created_at_in_seconds,
        process_initiator_user.username.label("process_initiator_username"),
        GroupModel.identifier.label("assigned_user_group_identifier"),
        # func.max does not seem to return columns so we need to call both
        func.max(ProcessInstanceModel.process_model_identifier),
        func.max(ProcessInstanceModel.status.label("process_instance_status")),  # type: ignore
        func.max(ProcessInstanceModel.updated_at_in_seconds),
        func.max(ProcessInstanceModel.created_at_in_seconds),
        func.max(process_initiator_user.username.label("process_initiator_username")),
        func.max(GroupModel.identifier.label("assigned_user_group_identifier")),
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


def _munge_form_ui_schema_based_on_hidden_fields_in_task_data(task: Task) -> None:
    if task.form_ui_schema is None:
        task.form_ui_schema = {}

    if task.data and "form_ui_hidden_fields" in task.data:
        hidden_fields = task.data["form_ui_hidden_fields"]
        for hidden_field in hidden_fields:
            hidden_field_parts = hidden_field.split(".")
            relevant_depth_of_ui_schema = task.form_ui_schema
            for ii, hidden_field_part in enumerate(hidden_field_parts):
                if hidden_field_part not in relevant_depth_of_ui_schema:
                    relevant_depth_of_ui_schema[hidden_field_part] = {}
                relevant_depth_of_ui_schema = relevant_depth_of_ui_schema[
                    hidden_field_part
                ]
                if len(hidden_field_parts) == ii + 1:
                    relevant_depth_of_ui_schema["ui:widget"] = "hidden"


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

    _find_human_task_or_raise(process_instance_id, task_id)

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
        top_process_name = processor.find_process_model_process_name_by_task_name(
            task.process_identifier
        )
        bpmn_file_full_path = (
            ProcessInstanceProcessor.bpmn_file_full_path_from_bpmn_process_identifier(
                top_process_name
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
                    message=(
                        "Cannot find a form file for process_instance_id:"
                        f" {process_instance_id}, task_id: {task_id}"
                    ),
                    status_code=400,
                )
            )

        form_dict = _prepare_form_data(
            form_schema_file_name,
            spiff_task,
            process_model_with_form,
        )

        if task.data:
            _update_form_schema_with_task_data_as_needed(form_dict, task, spiff_task)

        if form_dict:
            task.form_schema = form_dict

        if form_ui_schema_file_name:
            ui_form_contents = _prepare_form_data(
                form_ui_schema_file_name,
                task,
                process_model_with_form,
            )
            if ui_form_contents:
                task.form_ui_schema = ui_form_contents

        _munge_form_ui_schema_based_on_hidden_fields_in_task_data(task)

    if task.properties and task.data and "instructionsForEndUser" in task.properties:
        if task.properties["instructionsForEndUser"]:
            try:
                task.properties["instructionsForEndUser"] = _render_jinja_template(
                    task.properties["instructionsForEndUser"], spiff_task
                )
            except WorkflowTaskException as wfe:
                wfe.add_note("Failed to render instructions for end user.")
                raise ApiError.from_workflow_exception(
                    "instructions_error", str(wfe), exp=wfe
                ) from wfe
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


def task_submit_shared(
    process_instance_id: int,
    task_id: str,
    body: Dict[str, Any],
    terminate_loop: bool = False,
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

    human_task = _find_human_task_or_raise(
        process_instance_id=process_instance_id,
        task_id=task_id,
        only_tasks_that_can_be_completed=True,
    )

    with sentry_sdk.start_span(op="task", description="complete_form_task"):
        processor.lock_process_instance("Web")
        ProcessInstanceService.complete_form_task(
            processor=processor,
            spiff_task=spiff_task,
            data=body,
            user=g.user,
            human_task=human_task,
        )
        processor.unlock_process_instance("Web")

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


def task_submit(
    process_instance_id: int,
    task_id: str,
    body: Dict[str, Any],
    terminate_loop: bool = False,
) -> flask.wrappers.Response:
    """Task_submit_user_data."""
    with sentry_sdk.start_span(
        op="controller_action", description="tasks_controller.task_submit"
    ):
        return task_submit_shared(process_instance_id, task_id, body, terminate_loop)


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

    potential_owner_usernames_from_group_concat_or_similar = (
        _get_potential_owner_usernames(assigned_user)
    )

    human_tasks = (
        human_tasks_query.add_columns(
            ProcessInstanceModel.process_model_identifier,
            ProcessInstanceModel.status.label("process_instance_status"),  # type: ignore
            ProcessInstanceModel.updated_at_in_seconds,
            ProcessInstanceModel.created_at_in_seconds,
            UserModel.username.label("process_initiator_username"),  # type: ignore
            GroupModel.identifier.label("assigned_user_group_identifier"),
            HumanTaskModel.task_name,
            HumanTaskModel.task_title,
            HumanTaskModel.process_model_display_name,
            HumanTaskModel.process_instance_id,
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


def _prepare_form_data(
    form_file: str, spiff_task: SpiffTask, process_model: ProcessModelInfo
) -> dict:
    """Prepare_form_data."""
    if spiff_task.data is None:
        return {}

    file_contents = SpecFileService.get_data(process_model, form_file).decode("utf-8")
    try:
        form_contents = _render_jinja_template(file_contents, spiff_task)
        try:
            # form_contents is a str
            hot_dict: dict = json.loads(form_contents)
            return hot_dict
        except Exception as exception:
            raise (
                ApiError(
                    error_code="error_loading_form",
                    message=(
                        f"Could not load form schema from: {form_file}."
                        f" Error was: {str(exception)}"
                    ),
                    status_code=400,
                )
            ) from exception
    except WorkflowTaskException as wfe:
        wfe.add_note(f"Error in Json Form File '{form_file}'")
        api_error = ApiError.from_workflow_exception(
            "instructions_error", str(wfe), exp=wfe
        )
        api_error.file_name = form_file
        raise api_error


def _render_jinja_template(unprocessed_template: str, spiff_task: SpiffTask) -> str:
    """Render_jinja_template."""
    jinja_environment = jinja2.Environment(
        autoescape=True, lstrip_blocks=True, trim_blocks=True
    )
    try:
        template = jinja_environment.from_string(unprocessed_template)
        return template.render(**spiff_task.data)
    except jinja2.exceptions.TemplateError as template_error:
        wfe = WorkflowTaskException(
            str(template_error), task=spiff_task, exception=template_error
        )
        if isinstance(template_error, TemplateSyntaxError):
            wfe.line_number = template_error.lineno
            wfe.error_line = template_error.source.split("\n")[
                template_error.lineno - 1
            ]
        wfe.add_note(
            "Jinja2 template errors can happen when trying to displaying task data"
        )
        raise wfe from template_error
    except Exception as error:
        type, value, tb = exc_info()
        wfe = WorkflowTaskException(
            str(error), task=spiff_task, exception=error
        )
        while tb:
            if tb.tb_frame.f_code.co_filename == '<template>':
                wfe.line_number = tb.tb_lineno
                wfe.error_line = unprocessed_template.split("\n")[tb.tb_lineno - 1]
            tb = tb.tb_next
        wfe.add_note(
            "Jinja2 template errors can happen when trying to displaying task data"
        )
        raise wfe from error


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
    in_dict: dict, task: Task, spiff_task: SpiffTask
) -> None:
    """Update_nested."""
    if task.data is None:
        return None

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

                            if task_data_var not in task.data:
                                wte = WorkflowTaskException(
                                    (
                                        "Error building form. Attempting to create a"
                                        " selection list with options from variable"
                                        f" '{task_data_var}' but it doesn't exist in"
                                        " the Task Data."
                                    ),
                                    task=spiff_task,
                                )
                                raise (
                                    ApiError.from_workflow_exception(
                                        error_code="missing_task_data_var",
                                        message=str(wte),
                                        exp=wte,
                                    )
                                )

                            select_options_from_task_data = task.data.get(task_data_var)
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
            _update_form_schema_with_task_data_as_needed(value, task, spiff_task)
        elif isinstance(value, list):
            for o in value:
                if isinstance(o, dict):
                    _update_form_schema_with_task_data_as_needed(o, task, spiff_task)


def _get_potential_owner_usernames(assigned_user: AliasedClass) -> Any:
    """_get_potential_owner_usernames."""
    potential_owner_usernames_from_group_concat_or_similar = func.group_concat(
        assigned_user.username.distinct()
    ).label("potential_owner_usernames")
    db_type = current_app.config.get("SPIFF_DATABASE_TYPE")

    if db_type == "postgres":
        potential_owner_usernames_from_group_concat_or_similar = func.string_agg(
            assigned_user.username.distinct(), ", "
        ).label("potential_owner_usernames")

    return potential_owner_usernames_from_group_concat_or_similar


def _find_human_task_or_raise(
    process_instance_id: int,
    task_id: str,
    only_tasks_that_can_be_completed: bool = False,
) -> HumanTaskModel:
    if only_tasks_that_can_be_completed:
        human_task_query = HumanTaskModel.query.filter_by(
            process_instance_id=process_instance_id, task_id=task_id, completed=False
        )
    else:
        human_task_query = HumanTaskModel.query.filter_by(
            process_instance_id=process_instance_id, task_id=task_id
        )

    human_task: HumanTaskModel = human_task_query.first()
    if human_task is None:
        raise (
            ApiError(
                error_code="no_human_task",
                message=(
                    f"Cannot find a task to complete for task id '{task_id}' and"
                    f" process instance {process_instance_id}."
                ),
                status_code=500,
            )
        )
    return human_task
