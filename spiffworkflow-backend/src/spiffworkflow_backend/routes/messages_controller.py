import json
from typing import Any

import flask.wrappers
from flask import g
from flask import jsonify
from flask import make_response
from flask.wrappers import Response
from SpiffWorkflow.bpmn.specs.mixins import StartEventMixin  # type: ignore

from spiffworkflow_backend import db
from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.message_instance import MessageInstanceModel
from spiffworkflow_backend.models.message_triggerable_process_model import MessageTriggerableProcessModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModelSchema
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.services.message_service import MessageService
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.spec_file_service import SpecFileService
from spiffworkflow_backend.services.task_service import TaskService


def message_instance_list(
    process_instance_id: int | None = None,
    page: int = 1,
    per_page: int = 100,
) -> flask.wrappers.Response:
    # to make sure the process instance exists
    message_instances_query = MessageInstanceModel.query

    if process_instance_id:
        message_instances_query = message_instances_query.filter_by(process_instance_id=process_instance_id)

    message_instances = (
        message_instances_query.order_by(
            MessageInstanceModel.created_at_in_seconds.desc(),  # type: ignore
            MessageInstanceModel.id.desc(),  # type: ignore
        )
        .outerjoin(ProcessInstanceModel)  # Not all messages were created by a process
        .add_columns(
            ProcessInstanceModel.process_model_identifier,
            ProcessInstanceModel.process_model_display_name,
        )
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    response_json = {
        "results": message_instances.items,
        "pagination": {
            "count": len(message_instances.items),
            "total": message_instances.total,
            "pages": message_instances.pages,
        },
    }

    return make_response(jsonify(response_json), 200)


# body: {
#   payload: dict,
#   process_instance_id: Optional[int],
# }
#
# For example:
# curl 'http://localhost:7000/v1.0/messages/gogo' \
#  -H 'authorization: Bearer [FIXME]' \
#  -H 'content-type: application/json' \
#  --data-raw '{"payload":{"sure": "yes", "food": "spicy"}}'
def message_send(
    modified_message_name: str,
    body: dict[str, Any],
    execution_mode: str | None = None,
) -> flask.wrappers.Response:
    receiver_message = _run_process_model_from_message(modified_message_name, body, execution_mode)
    process_instance = ProcessInstanceModel.query.filter_by(id=receiver_message.process_instance_id).first()
    response_json = {
        "task_data": process_instance.get_data(),
        "process_instance": ProcessInstanceModelSchema().dump(process_instance),
    }
    return Response(
        json.dumps(response_json),
        status=200,
        mimetype="application/json",
    )


def message_form_show(
    modified_message_name: str,
) -> flask.wrappers.Response:
    message_triggerable_process_model = _find_message_triggerable_process_model(modified_message_name)

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
    receiver_message = _run_process_model_from_message(modified_message_name, body, execution_mode)
    process_instance = ProcessInstanceModel.query.filter_by(id=receiver_message.process_instance_id).first()
    next_human_task_assigned_to_me = TaskService.next_human_task_for_user(process_instance.id, g.user.id)

    response_json = {
        "next_task": next_human_task_assigned_to_me,
        "instructions": None,
    }
    return make_response(jsonify(response_json), 200)


def _find_message_triggerable_process_model(modified_message_name: str) -> MessageTriggerableProcessModel:
    message_name, process_group_identifier = MessageInstanceModel.split_modified_message_name(modified_message_name)
    potential_matches = MessageTriggerableProcessModel.query.filter_by(message_name=message_name).all()
    actual_matches = []
    for potential_match in potential_matches:
        pgi, _ = potential_match.process_model_identifier.rsplit("/", 1)
        if pgi.startswith(process_group_identifier):
            actual_matches.append(potential_match)

    if len(actual_matches) == 0:
        raise (
            ApiError(
                error_code="message_triggerable_process_model_not_found",
                message=(
                    f"Could not find a message triggerable process model for {modified_message_name} in the scope of group"
                    f" {process_group_identifier}"
                ),
                status_code=400,
            )
        )

    if len(actual_matches) > 1:
        message_names = [f"{m.process_model_identifier} - {m.message_name}" for m in actual_matches]
        raise (
            ApiError(
                error_code="multiple_message_triggerable_process_models_found",
                message=f"Found {len(actual_matches)}. Expected 1. Found entries: {message_names}",
                status_code=400,
            )
        )
    mtp: MessageTriggerableProcessModel = actual_matches[0]
    return mtp


def _get_json_contents_from_file(file_name: str, process_model: ProcessModelInfo) -> dict:
    contents = SpecFileService.get_data(process_model, file_name).decode("utf-8")
    return dict(json.loads(contents))


def _run_process_model_from_message(
    modified_message_name: str,
    body: dict[str, Any],
    execution_mode: str | None = None,
) -> MessageInstanceModel:
    message_name, _process_group_identifier = MessageInstanceModel.split_modified_message_name(modified_message_name)

    # Create the send message
    # TODO: support the full message id - including process group - in message instance
    message_instance = MessageInstanceModel(
        message_type="send",
        name=message_name,
        payload=body,
        user_id=g.user.id,
    )
    db.session.add(message_instance)
    db.session.commit()
    try:
        receiver_message = MessageService.correlate_send_message(message_instance, execution_mode=execution_mode)
    except Exception as e:
        db.session.delete(message_instance)
        db.session.commit()
        raise e
    if not receiver_message:
        db.session.delete(message_instance)
        db.session.commit()
        raise (
            ApiError(
                error_code="message_not_accepted",
                message=(
                    "No running process instances correlate with the given message"
                    f" name of '{modified_message_name}'.  And this message name is not"
                    " currently associated with any process Start Event. Nothing"
                    " to do."
                ),
                status_code=400,
            )
        )
    return receiver_message
