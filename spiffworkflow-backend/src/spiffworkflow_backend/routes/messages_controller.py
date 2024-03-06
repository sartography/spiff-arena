"""APIs for dealing with process groups, process models, and process instances."""
import json
from typing import Any

import flask.wrappers
from flask import g
from flask import jsonify
from flask import make_response
from flask.wrappers import Response

from spiffworkflow_backend import db
from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.exceptions.process_entity_not_found_error import ProcessEntityNotFoundError
from spiffworkflow_backend.models.message_instance import MessageInstanceModel
from spiffworkflow_backend.models.message_model import CorrelationKeySchema
from spiffworkflow_backend.models.message_model import CorrelationPropertySchema
from spiffworkflow_backend.models.message_model import MessageSchema
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModelSchema
from spiffworkflow_backend.models.reference_cache import ReferenceCacheModel
from spiffworkflow_backend.models.reference_cache import ReferenceSchema
from spiffworkflow_backend.models.reference_cache import ReferenceType
from spiffworkflow_backend.services.message_service import MessageService
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.reference_cache_service import ReferenceCacheService


def reference_cache_list(
    cache_type: str,
    relative_location: str | None = None,
    page: int = 1,
    per_page: int = 100,
) -> flask.wrappers.Response:
    query = ReferenceCacheModel.basic_query().filter_by(type=cache_type)
    if relative_location:
        locations = ReferenceCacheService.upsearch_locations(relative_location)
        query = query.filter(ReferenceCacheModel.relative_location.in_(locations))

    results = query.paginate(page=page, per_page=per_page, error_out=False)
    response_json = {
        "results": ReferenceSchema(many=True).dump(results.items),
        "pagination": {
            "count": len(results.items),
            "total": results.total,
            "pages": results.pages,
        },
    }
    return make_response(jsonify(response_json), 200)


def message_model_list_old(
    relative_location: str | None = None,
    page: int = 1,
    per_page: int = 100,
) -> flask.wrappers.Response:
    return reference_cache_list(
        cache_type=ReferenceType.message.value,
        relative_location=relative_location,
        page=page,
        per_page=per_page,
    )


def message_model_list(relative_location: str | None = None) -> flask.wrappers.Response:
    # Returns all the messages, correlation keys, and correlation properties that exist at the given
    # relative location or higher in the directory tree, presents it in the same format as you would
    # find in a single process group file.
    locations = ReferenceCacheService.upsearch_locations(relative_location)
    messages = []
    correlation_keys = []
    correlation_properties = []
    for loc in locations:
        try:
            process_group = ProcessModelService.get_process_group(loc)
            if process_group.messages is not None:
                messages.extend(process_group.messages)
            if process_group.correlation_properties is not None:
                correlation_properties.extend(process_group.correlation_properties)
            if process_group.correlation_keys is not None:
                correlation_keys.extend(process_group.correlation_keys)
        except ProcessEntityNotFoundError:
            pass
    response_json = {
        "messages": MessageSchema(many=True).dump(messages),
        "correlation_keys": CorrelationKeySchema(many=True).dump(correlation_keys),
        "correlation_properties": CorrelationPropertySchema(many=True).dump(correlation_properties),
    }
    return make_response(jsonify(response_json), 200)


def correlation_key_list(
    relative_location: str | None = None,
    page: int = 1,
    per_page: int = 100,
) -> flask.wrappers.Response:
    return reference_cache_list(
        cache_type=ReferenceType.correlation_key.value,
        relative_location=relative_location,
        page=page,
        per_page=per_page,
    )


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
    message_name: str,
    body: dict[str, Any],
) -> flask.wrappers.Response:
    if "payload" not in body:
        raise (
            ApiError(
                error_code="missing_payload",
                message="Please include a 'payload' in the JSON body that contains the message contents.",
                status_code=400,
            )
        )

    process_instance = None

    # Create the send message
    message_instance = MessageInstanceModel(
        message_type="send",
        name=message_name,
        payload=body["payload"],
        user_id=g.user.id,
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
                    "No running process instances correlate with the given message"
                    f" name of '{message_name}'.  And this message name is not"
                    " currently associated with any process Start Event. Nothing"
                    " to do."
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
