import json
from typing import Any

import flask.wrappers
from flask import jsonify
from flask import make_response
from flask.wrappers import Response
from flask_sqlalchemy.pagination import QueryPagination

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.message_instance import MessageInstanceModel
from spiffworkflow_backend.models.message_model import MessageCorrelationPropertyModel
from spiffworkflow_backend.models.message_model import MessageModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.services.message_service import MessageService
from spiffworkflow_backend.services.upsearch_service import UpsearchService
from spiffworkflow_backend.utils.api_logging import log_api_interaction


def message_model_list_all() -> flask.wrappers.Response:
    return _get_message_models(MessageModel.query.all())


def message_model_list_from_root() -> flask.wrappers.Response:
    return message_model_list()


def message_model_list(relative_location: str | None = None) -> flask.wrappers.Response:
    # Returns all the messages and correlation properties that exist at the given
    # relative location or higher in the directory tree.

    loc = relative_location.replace(":", "/") if relative_location else ""
    locations = UpsearchService.upsearch_locations(loc)
    messages = db.session.query(MessageModel).filter(MessageModel.location.in_(locations)).order_by(MessageModel.identifier).all()  # type: ignore
    return _get_message_models(messages)


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
    return _create_message_instance_response(message_instances)


def message_instance_search(
    body: dict[str, Any],
    process_instance_id: int | None = None,
    page: int = 1,
    per_page: int = 100,
) -> flask.wrappers.Response:
    message_instances_query = MessageInstanceModel.query
    if process_instance_id:
        message_instances_query = message_instances_query.filter_by(process_instance_id=process_instance_id)

    name = body.get("name")
    if name is not None and isinstance(name, str):
        message_instances_query = message_instances_query.filter_by(name=name)

    message_type = body.get("message_type")
    if message_type and isinstance(message_type, list | tuple):
        message_instances_query = message_instances_query.filter(MessageInstanceModel.message_type.in_(message_type))  # type: ignore

    status = body.get("status")
    if status and isinstance(status, list | tuple):
        message_instances_query = message_instances_query.filter(MessageInstanceModel.status.in_(status))  # type: ignore

    created_after = body.get("created_after")
    if created_after is not None and isinstance(created_after, int | float):
        message_instances_query = message_instances_query.filter(MessageInstanceModel.created_at_in_seconds >= created_after)

    created_before = body.get("created_before")
    if created_before is not None and isinstance(created_before, int | float):
        message_instances_query = message_instances_query.filter(MessageInstanceModel.created_at_in_seconds <= created_before)

    process_model_identifier = body.get("process_model_identifier")
    if process_model_identifier is not None and isinstance(process_model_identifier, str):
        message_instances_query = message_instances_query.filter(
            ProcessInstanceModel.process_model_identifier == process_model_identifier
        )

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
    return _create_message_instance_response(message_instances)


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
@log_api_interaction
def message_send(
    modified_message_name: str,
    body: dict[str, Any],
    execution_mode: str | None = None,
) -> flask.wrappers.Response:
    receiver_message = MessageService.run_process_model_from_message(modified_message_name, body, execution_mode)
    process_instance = ProcessInstanceModel.query.filter_by(id=receiver_message.process_instance_id).first()
    response_json = {
        "task_data": process_instance.get_data(),
        "process_instance": process_instance.serialized(),
    }
    return Response(
        json.dumps(response_json),
        status=200,
        mimetype="application/json",
    )


def get_process_model_for_message(modified_message_name: str) -> flask.wrappers.Response:
    message_triggerable_process_model = MessageService.find_message_triggerable_process_model(modified_message_name)
    process_model_response = {
        "process_model_identifier": message_triggerable_process_model.process_model_identifier,
        "file_name": message_triggerable_process_model.file_name,
    }
    return make_response(jsonify(process_model_response), 200)


def _get_message_models(messages: list[MessageModel]) -> flask.wrappers.Response:
    def correlation_property_response(correlation_property: MessageCorrelationPropertyModel) -> dict[str, str]:
        return {
            "identifier": correlation_property.identifier,
            "retrieval_expression": correlation_property.retrieval_expression,
        }

    def message_response(message: MessageModel) -> dict[str, Any]:
        return {
            "identifier": message.identifier,
            "location": message.location,
            "schema": message.schema,
            "correlation_properties": [correlation_property_response(cp) for cp in message.correlation_properties],
        }

    return make_response(jsonify({"messages": [message_response(m) for m in messages]}), 200)


def _create_message_instance_response(message_instances: QueryPagination) -> flask.Response:
    response_json = {
        "results": message_instances.items,
        "pagination": {
            "count": len(message_instances.items),
            "total": message_instances.total,
            "pages": message_instances.pages,
        },
    }
    return make_response(jsonify(response_json), 200)
