import json
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
from spiffworkflow_backend.services.message_service import MessageService
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.spec_file_service import SpecFileService
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

    response_body = {}
    extensions = matching_start_tasks[0].task_spec.extensions
    if "properties" in extensions:
        properties = extensions["properties"]
        if "formJsonSchemaFilename" in properties:
            form_schema_file_name = properties["formJsonSchemaFilename"]
            response_body["form_schema"] = _get_json_contents_from_file(form_schema_file_name, process_model)
        if "formUiSchemaFilename" in properties:
            form_ui_schema_file_name = properties["formUiSchemaFilename"]
            response_body["form_ui_schema"] = _get_json_contents_from_file(form_ui_schema_file_name, process_model)

    return make_response(jsonify(response_body), 200)


def message_form_submit(
    modified_message_name: str,
    body: dict[str, Any],
    execution_mode: str | None = None,
) -> flask.wrappers.Response:
    receiver_message = MessageService.run_process_model_from_message(modified_message_name, body, execution_mode)
    process_instance = ProcessInstanceModel.query.filter_by(id=receiver_message.process_instance_id).first()
    next_human_task_assigned_to_me = TaskService.next_human_task_for_user(process_instance.id, g.user.id)

    response_json = {
        "next_task": next_human_task_assigned_to_me,
        "instructions": None,
    }
    return make_response(jsonify(response_json), 200)


def _get_json_contents_from_file(file_name: str, process_model: ProcessModelInfo) -> dict:
    contents = SpecFileService.get_data(process_model, file_name).decode("utf-8")
    return dict(json.loads(contents))
