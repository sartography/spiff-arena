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

from spiffworkflow_backend import db
from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.message_instance import MessageInstanceModel, MessageStatuses
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModelSchema
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
        .outerjoin(ProcessInstanceModel) # Not all messages were created by a process
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
def message_send(
    message_name: str,
    body: Dict[str, Any],
) -> flask.wrappers.Response:
    """Message_start."""

    if "payload" not in body:
        raise (
            ApiError(
                error_code="missing_payload",
                message=(
                    "Please include a 'payload' in the JSON body that contains the"
                    " message contents."
                ),
                status_code=400,
            )
        )

    process_instance = None

    # Create the send message
    message_instance = MessageInstanceModel(
        process_instance_id=None,
        message_type="send",
        name=message_name,
        payload=body['payload'],
        user_id=g.user.id,
        correlations=[],
    )
    db.session.add(message_instance)
    db.session.commit()
    try:
        receiver_message = MessageService.correlate_send_message(message_instance)
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
                        "No running process instances correlate with the given message name of"
                        f" '{message_name}'.  And this message name is not"
                        " currently associated with any process Start Event. Nothing to do."
                    ),
                    status_code=400,
                )
        )

    process_instance = ProcessInstanceModel.query.filter_by(id=receiver_message.process_instance_id).first()
    return Response(
        json.dumps(ProcessInstanceModelSchema().dump(process_instance)),
        status=200,
        mimetype="application/json",
    )