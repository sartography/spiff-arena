from typing import Any

import flask.wrappers
from flask import g
from flask import jsonify
from flask import make_response
from SpiffWorkflow.bpmn.specs.mixins import StartEventMixin  # type: ignore

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.models.task import TaskModel  # noqa: F401
from spiffworkflow_backend.routes.process_api_blueprint import _prepare_form_data
from spiffworkflow_backend.routes.process_api_blueprint import _task_submit_shared
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
    response_body = _get_form_and_prepare_data(extensions=extensions, process_model=process_model)

    return make_response(jsonify(response_body), 200)


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
    if next_human_task_assigned_to_me:
        task_guid = next_human_task_assigned_to_me.task_guid
        process_model = ProcessModelService.get_process_model(process_instance.process_model_identifier)
        next_form_contents = _get_form_and_prepare_data(
            process_model=process_model, task_guid=next_human_task_assigned_to_me.task_guid, process_instance=process_instance
        )

    response_json = {
        "form": next_form_contents,
        "task_guid": task_guid,
        "process_instance_id": process_instance.id,
        "confirmation_message_markdown": None,
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
    if "next_task_assigned_to_me" in response_item:
        next_task_assigned_to_me = response_item["next_task_assigned_to_me"]
        process_instance = ProcessInstanceModel.query.filter_by(id=process_instance_id).first()
        next_task_guid = next_task_assigned_to_me.id
        process_model = ProcessModelService.get_process_model(process_instance.process_model_identifier)
        next_form_contents = _get_form_and_prepare_data(
            process_model=process_model, task_guid=next_task_assigned_to_me.task_guid, process_instance=process_instance
        )

    response_json = {
        "form": next_form_contents,
        "task_guid": next_task_guid,
        "process_instance_id": process_instance_id,
        "confirmation_message_markdown": response_item.get("guest_confirmation"),
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

    form_contents = {}
    if extension_list and "properties" in extension_list:
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
    return form_contents
