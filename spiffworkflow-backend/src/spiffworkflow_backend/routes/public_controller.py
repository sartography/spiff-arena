from typing import Any

import flask.wrappers
from flask import g
from flask import jsonify
from flask import make_response
from SpiffWorkflow.bpmn.specs.mixins import StartEventMixin  # type: ignore
from SpiffWorkflow.util.task import TaskState  # type: ignore

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.human_task_user import HumanTaskUserAddedBy
from spiffworkflow_backend.models.human_task_user import HumanTaskUserModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.models.task import TaskModel
from spiffworkflow_backend.routes.process_api_blueprint import _get_task_model_for_request
from spiffworkflow_backend.routes.process_api_blueprint import _prepare_form_data
from spiffworkflow_backend.routes.process_api_blueprint import _task_submit_shared
from spiffworkflow_backend.services.jinja_service import JinjaService
from spiffworkflow_backend.services.message_service import MessageService
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.task_service import TaskService


def message_form_show(
    modified_message_name: str,
) -> flask.wrappers.Response:
    message_triggerable_process_model = MessageService.find_message_triggerable_process_model(modified_message_name)

    process_instance = ProcessInstanceModel(
        status=ProcessInstanceStatus.not_started.value,
        process_initiator_id=None,
        process_model_identifier=message_triggerable_process_model.process_model_identifier,
        persistence_level="none",
    )
    processor = ProcessInstanceProcessor(process_instance)
    start_tasks = processor.bpmn_process_instance.get_tasks(spec_class=StartEventMixin)
    matching_start_tasks = [
        t for t in start_tasks if t.task_spec.event_definition.name == message_triggerable_process_model.message_name
    ]
    if len(matching_start_tasks) == 0:
        raise (
            ApiError(
                error_code="message_start_event_not_found",
                message=(
                    f"Could not find a message start event for message '{message_triggerable_process_model.message_name}' in"
                    f" process model '{message_triggerable_process_model.process_model_identifier}'."
                ),
                status_code=400,
            )
        )

    process_model = ProcessModelService.get_process_model(message_triggerable_process_model.process_model_identifier)
    extensions = matching_start_tasks[0].task_spec.extensions
    form = _get_form_and_prepare_data(extensions=extensions, process_model=process_model)

    response_json = {
        "form": form,
        "task_guid": None,
        "process_instance_id": None,
        "confirmation_message_markdown": None,
    }
    return make_response(jsonify(response_json), 200)


def message_form_submit(
    modified_message_name: str,
    body: dict[str, Any],
    execution_mode: str | None = None,
) -> flask.wrappers.Response:
    receiver_message = MessageService.run_process_model_from_message(modified_message_name, body, execution_mode)
    process_instance = ProcessInstanceModel.query.filter_by(id=receiver_message.process_instance_id).first()
    next_human_task_assigned_to_me = TaskService.next_human_task_for_user(process_instance.id, g.user.id)

    next_form_contents = None
    task_guid = None
    confirmation_message_markdown = None
    if next_human_task_assigned_to_me:
        task_guid = next_human_task_assigned_to_me.task_guid
        process_model = ProcessModelService.get_process_model(process_instance.process_model_identifier)
        next_form_contents = _get_form_and_prepare_data(
            process_model=process_model, task_guid=next_human_task_assigned_to_me.task_guid, process_instance=process_instance
        )
    else:
        processor = ProcessInstanceProcessor(process_instance)
        start_tasks = processor.bpmn_process_instance.get_tasks(spec_class=StartEventMixin, state=TaskState.COMPLETED)
        matching_start_tasks = [t for t in start_tasks if t.task_spec.event_definition.name == receiver_message.name]
        if len(matching_start_tasks) > 0:
            spiff_task = matching_start_tasks[0]
            task_model = TaskModel.query.filter_by(guid=str(spiff_task.id)).first()
            spiff_task_extensions = spiff_task.task_spec.extensions
            if "guestConfirmation" in spiff_task_extensions and spiff_task_extensions["guestConfirmation"]:
                confirmation_message_markdown = JinjaService.render_jinja_template(
                    spiff_task.task_spec.extensions["guestConfirmation"], task_model
                )

    response_json = {
        "form": next_form_contents,
        "task_guid": task_guid,
        "process_instance_id": process_instance.id,
        "confirmation_message_markdown": confirmation_message_markdown,
    }
    return make_response(jsonify(response_json), 200)


def form_submit(
    process_instance_id: int,
    task_guid: str,
    body: dict[str, Any],
    execution_mode: str | None = None,
) -> flask.wrappers.Response:
    response_item = _task_submit_shared(process_instance_id, task_guid, body, execution_mode=execution_mode)

    next_form_contents = None
    next_task_guid = None

    next_task_assigned_to_me = None
    if "next_task_assigned_to_me" in response_item:
        next_task_assigned_to_me = response_item["next_task_assigned_to_me"]
    elif "next_task" in response_item:
        task_model = TaskModel.query.filter_by(guid=str(response_item["next_task"].id)).first()
        if _assign_task_if_guest(task_model):
            next_task_assigned_to_me = response_item["next_task"]

    if next_task_assigned_to_me is not None:
        process_instance = ProcessInstanceModel.query.filter_by(id=process_instance_id).first()
        next_task_guid = str(next_task_assigned_to_me.id)
        process_model = ProcessModelService.get_process_model(process_instance.process_model_identifier)
        next_form_contents = _get_form_and_prepare_data(
            process_model=process_model, task_guid=next_task_guid, process_instance=process_instance
        )

    response_json = {
        "form": next_form_contents,
        "task_guid": next_task_guid,
        "process_instance_id": process_instance_id,
        "confirmation_message_markdown": response_item.get("guest_confirmation"),
    }
    return make_response(jsonify(response_json), 200)


def form_show(
    process_instance_id: int,
    task_guid: str,
) -> flask.wrappers.Response:
    task_model = _get_task_model_for_request(
        process_instance_id=process_instance_id,
        task_guid=task_guid,
        with_form_data=True,
    )
    if task_model is None or not task_model.allows_guest(task_model.process_instance_id):
        raise (
            ApiError(
                error_code="task_not_found",
                message=f"Could not find completable task for {task_guid} in process_instance {process_instance_id}.",
                status_code=404,
            )
        )

    _assign_task_if_guest(task_model)

    instructions_for_end_user = None
    if task_model.extensions:
        instructions_for_end_user = task_model.extensions["instructionsForEndUser"]

    form = {
        "form_schema": task_model.form_schema,
        "form_ui_schema": task_model.form_ui_schema,
        "instructions_for_end_user": instructions_for_end_user,
    }

    response_json = {
        "form": form,
        "task_guid": task_guid,
        "process_instance_id": process_instance_id,
        "confirmation_message_markdown": None,
    }
    return make_response(jsonify(response_json), 200)


def _get_form_and_prepare_data(
    process_model: ProcessModelInfo,
    extensions: dict | None = None,
    task_guid: str | None = None,
    process_instance: ProcessInstanceModel | None = None,
) -> dict:
    task_model = None
    extension_list = extensions
    if task_guid and process_instance:
        task_model = TaskModel.query.filter_by(guid=task_guid, process_instance_id=process_instance.id).first()
        task_model.data = task_model.json_data()
        extension_list = TaskService.get_extensions_from_task_model(task_model)

    revision = None
    if process_instance:
        revision = process_instance.bpmn_version_control_identifier

    form_contents: dict = {}
    if extension_list:
        if "properties" in extension_list:
            properties = extension_list["properties"]
            if "formJsonSchemaFilename" in properties:
                form_schema_file_name = properties["formJsonSchemaFilename"]
                form_contents["form_schema"] = _prepare_form_data(
                    form_file=form_schema_file_name,
                    task_model=task_model,
                    process_model=process_model,
                    revision=revision,
                )
            if "formUiSchemaFilename" in properties:
                form_ui_schema_file_name = properties["formUiSchemaFilename"]
                form_contents["form_ui_schema"] = _prepare_form_data(
                    form_file=form_ui_schema_file_name,
                    task_model=task_model,
                    process_model=process_model,
                    revision=revision,
                )
        if "instructionsForEndUser" in extension_list and extension_list["instructionsForEndUser"]:
            task_data = {}
            if task_model is not None and task_model.data:
                task_data = task_model.data
            form_contents["instructions_for_end_user"] = JinjaService.render_jinja_template(
                extension_list["instructionsForEndUser"], task_data=task_data
            )
    return form_contents


def _assign_task_if_guest(task_model: TaskModel) -> bool:
    if not task_model.allows_guest(task_model.process_instance_id):
        return False

    human_task_user = (
        HumanTaskUserModel.query.filter_by(user_id=g.user.id)
        .join(HumanTaskModel, HumanTaskModel.id == HumanTaskUserModel.human_task_id)
        .filter(HumanTaskModel.task_guid == task_model.guid)
        .first()
    )
    if human_task_user is None:
        human_task = HumanTaskModel.query.filter_by(
            task_guid=task_model.guid, process_instance_id=task_model.process_instance_id
        ).first()
        if human_task is None:
            raise (
                ApiError(
                    error_code="completable_task_not_found",
                    message=(
                        f"Could not find completable task for {task_model.guid} in process_instance"
                        f" {task_model.process_instance_id}."
                    ),
                    status_code=400,
                )
            )
        human_task_user = HumanTaskUserModel(user_id=g.user.id, human_task=human_task, added_by=HumanTaskUserAddedBy.guest.value)
        db.session.add(human_task_user)
        db.session.commit()
    return True
