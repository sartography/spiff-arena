"""APIs for dealing with process groups, process models, and process instances."""
import json
from flask import current_app
from typing import Any
from typing import Optional

import flask.wrappers
from flask import g
from flask import jsonify
from flask import make_response
from flask.wrappers import Response
from flask_bpmn.api.api_error import ApiError

from spiffworkflow_backend.exceptions.process_entity_not_found_error import (
    ProcessEntityNotFoundError,
)
from spiffworkflow_backend.models.process_group import ProcessGroup
from spiffworkflow_backend.models.process_group import ProcessGroupSchema
from spiffworkflow_backend.routes.process_api_blueprint import _commit_and_push_to_git
from spiffworkflow_backend.routes.process_api_blueprint import (
    _un_modify_modified_process_model_id,
)
from spiffworkflow_backend.services.process_model_service import ProcessModelService


def process_group_create(body: dict) -> flask.wrappers.Response:
    """Add_process_group."""
    process_group = ProcessGroup(**body)
    ProcessModelService.add_process_group(process_group)
    _commit_and_push_to_git(
        f"User: {g.user.username} added process group {process_group.id}"
    )
    return make_response(jsonify(process_group), 201)


def process_group_delete(modified_process_group_id: str) -> flask.wrappers.Response:
    """Process_group_delete."""
    process_group_id = _un_modify_modified_process_model_id(modified_process_group_id)
    ProcessModelService().process_group_delete(process_group_id)
    _commit_and_push_to_git(
        f"User: {g.user.username} deleted process group {process_group_id}"
    )
    return Response(json.dumps({"ok": True}), status=200, mimetype="application/json")


def process_group_update(
    modified_process_group_id: str, body: dict
) -> flask.wrappers.Response:
    """Process Group Update."""
    body_include_list = ["display_name", "description"]
    body_filtered = {
        include_item: body[include_item]
        for include_item in body_include_list
        if include_item in body
    }

    process_group_id = _un_modify_modified_process_model_id(modified_process_group_id)
    process_group = ProcessGroup(id=process_group_id, **body_filtered)
    ProcessModelService.update_process_group(process_group)
    _commit_and_push_to_git(
        f"User: {g.user.username} updated process group {process_group_id}"
    )
    return make_response(jsonify(process_group), 200)


def process_group_list(
    process_group_identifier: Optional[str] = None, page: int = 1, per_page: int = 100
) -> flask.wrappers.Response:
    """Process_group_list."""
    if process_group_identifier is not None:
        process_groups = ProcessModelService.get_process_groups(
            process_group_identifier
        )
    else:
        process_groups = ProcessModelService.get_process_groups()
    batch = ProcessModelService().get_batch(
        items=process_groups, page=page, per_page=per_page
    )
    pages = len(process_groups) // per_page
    remainder = len(process_groups) % per_page
    if remainder > 0:
        pages += 1

    response_json = {
        "results": ProcessGroupSchema(many=True).dump(batch),
        "pagination": {
            "count": len(batch),
            "total": len(process_groups),
            "pages": pages,
        },
    }
    # response = make_response(jsonify(response_json), 200)
    response = Response(json.dumps(response_json), status=200, mimetype="application/json")
    current_app.logger.info("SETTING COOKIE")
    response.set_cookie('TEST_COOKIE', 'HEY1', domain='spiff.localdev')
    return response


def process_group_show(
    modified_process_group_id: str,
) -> Any:
    """Process_group_show."""
    process_group_id = _un_modify_modified_process_model_id(modified_process_group_id)
    try:
        process_group = ProcessModelService.get_process_group(process_group_id)
    except ProcessEntityNotFoundError as exception:
        raise (
            ApiError(
                error_code="process_group_cannot_be_found",
                message=f"Process group cannot be found: {process_group_id}",
                status_code=400,
            )
        ) from exception

    process_group.parent_groups = ProcessModelService.get_parent_group_array(
        process_group.id
    )
    return make_response(jsonify(process_group), 200)


def process_group_move(
    modified_process_group_identifier: str, new_location: str
) -> flask.wrappers.Response:
    """Process_group_move."""
    original_process_group_id = _un_modify_modified_process_model_id(
        modified_process_group_identifier
    )
    new_process_group = ProcessModelService().process_group_move(
        original_process_group_id, new_location
    )
    _commit_and_push_to_git(
        f"User: {g.user.username} moved process group {original_process_group_id} to"
        f" {new_process_group.id}"
    )
    return make_response(jsonify(new_process_group), 200)
