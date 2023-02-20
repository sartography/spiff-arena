"""APIs for dealing with process groups, process models, and process instances."""
import json
from typing import Any
from typing import Dict
from typing import Optional

import flask.wrappers
from flask import g
from flask import jsonify
from flask import make_response
from flask.wrappers import Response

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.message_correlation import MessageCorrelationModel
from spiffworkflow_backend.models.message_correlation_property import MessageCorrelationPropertyModel
from spiffworkflow_backend.models.message_instance import MessageInstanceModel
from spiffworkflow_backend.models.message_model import MessageModel
from spiffworkflow_backend.models.message_triggerable_process_model import (
    MessageTriggerableProcessModel,
)
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModelSchema
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
from spiffworkflow_backend.routes.process_api_blueprint import (
    _find_process_instance_by_id_or_raise,
)
from spiffworkflow_backend.services.message_service import MessageService


def message_instance_list(
    process_instance_id: Optional[int] = None,
    page: int = 1,
    per_page: int = 100,
) -> flask.wrappers.Response:
    """Message_instance_list."""
    # to make sure the process instance exists
    message_instances_query = MessageInstanceModel.query

    if process_instance_id:
        message_instances_query = message_instances_query.filter_by(
            process_instance_id=process_instance_id
        )

    message_instances = (
        message_instances_query.order_by(
            MessageInstanceModel.created_at_in_seconds.desc(),  # type: ignore
            MessageInstanceModel.id.desc(),  # type: ignore
        )
        .join(MessageModel, MessageModel.id == MessageInstanceModel.message_model_id)
        .join(ProcessInstanceModel)
        .add_columns(
            MessageModel.identifier.label("message_identifier"),
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
def message_send(
    message_identifier: str,
    body: Dict[str, Any],
) -> flask.wrappers.Response:
    """Message_start."""
    message_model = MessageModel.query.filter_by(identifier=message_identifier).first()
    if message_model is None:
        raise (
            ApiError(
                error_code="unknown_message",
                message=f"Could not find message with identifier: {message_identifier}",
                status_code=404,
            )
        )

    if "payload" not in body:
        raise (
            ApiError(
                error_code="missing_payload",
                message="Please include a 'payload' in the JSON body that contains the message contents.",
                status_code=400,
            )
        )

    process_instance = None

    # Is there a running instance that is waiting for this message?
    message_instances = MessageInstanceModel.query.filter_by(message_model_id=message_model.id).all()

    # do any waiting message instances have matching correlations?
    matching_message = None
    for message_instance in message_instances:
        if message_instance.correlates_with_dictionary(body["payload"]):
            matching_message = message_instance

    process_instance = None
    if matching_message:
        process_instance = ProcessInstanceModel.query.filter_by(id = matching_message.process_instance_id).first()

    if matching_message and process_instance and process_instance.status != ProcessInstanceStatus.waiting.value:
        raise ApiError(
            error_code="message_not_accepted",
            message=(
                f"The process that can accept message '{message_identifier}' with the given correlation keys"
                f" is not currently waiting for that message.  It is currently in the a '{process_instance.status}' state."
            ),
            status_code=400,
        )
    elif matching_message and process_instance:
        MessageService.process_message_receive(
            message_instance, message_model.name, body["payload"]
        )
    else:
        # We don't have a process model waiting on this message, perhaps some process should be started?
        message_triggerable_process_model = (
            MessageTriggerableProcessModel.query.filter_by(
                message_model_id=message_model.id
            ).first()
        )
        if message_triggerable_process_model is None:
            raise (
                ApiError(
                    error_code="cannot_start_message",
                    message=(
                        f"No process instances correlate with the given message id of '{message_identifier}'.  "
                        f"And this message name is not currently associated with any process Start Event."),
                    status_code=400,
                )
            )
        process_instance = MessageService.process_message_triggerable_process_model(
            message_triggerable_process_model,
            message_model.name,
            body["payload"],
            g.user,
        )

    return Response(
        json.dumps(ProcessInstanceModelSchema().dump(process_instance)),
        status=200,
        mimetype="application/json",
    )
