"""APIs for dealing with process groups, process models, and process instances."""

import json
from typing import Any

import flask.wrappers
from flask import g
from flask import jsonify
from flask import make_response
from flask.wrappers import Response

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.exceptions.error import NotAuthorizedError
from spiffworkflow_backend.exceptions.process_entity_not_found_error import ProcessEntityNotFoundError
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.message_model import MessageModel
from spiffworkflow_backend.models.process_group import PROCESS_GROUP_KEYS_TO_UPDATE_FROM_API
from spiffworkflow_backend.models.process_group import ProcessGroup
from spiffworkflow_backend.models.process_group import ProcessGroupSchema
from spiffworkflow_backend.routes.process_api_blueprint import _commit_and_push_to_git
from spiffworkflow_backend.routes.process_api_blueprint import _un_modify_modified_process_model_id
from spiffworkflow_backend.services.authorization_service import AuthorizationService
from spiffworkflow_backend.services.message_definition_service import MessageDefinitionService
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.process_model_service import ProcessModelWithInstancesNotDeletableError
from spiffworkflow_backend.services.spec_file_service import SpecFileService
from spiffworkflow_backend.services.user_service import UserService


def process_group_create(body: dict) -> flask.wrappers.Response:
    process_group = ProcessGroup(**body)

    if ProcessModelService.is_process_model_identifier(process_group.id):
        raise ApiError(
            error_code="process_model_with_id_already_exists",
            message=f"Process Model with given id already exists: {process_group.id}",
            status_code=400,
        )

    if ProcessModelService.is_process_group_identifier(process_group.id):
        raise ApiError(
            error_code="process_group_with_id_already_exists",
            message=f"Process Group with given id already exists: {process_group.id}",
            status_code=400,
        )

    ProcessModelService.add_process_group(process_group)
    _commit_and_push_to_git(f"User: {g.user.username} added process group {process_group.id}")
    return make_response(jsonify(process_group), 201)


def process_group_delete(modified_process_group_id: str) -> flask.wrappers.Response:
    process_group_id = _un_modify_modified_process_model_id(modified_process_group_id)

    try:
        ProcessModelService.process_group_delete(process_group_id)

        # can't do this in the ProcessModelService due to circular imports
        SpecFileService.clear_caches_for_item(process_group_id=process_group_id)
        db.session.commit()

    except ProcessModelWithInstancesNotDeletableError as exception:
        raise ApiError(
            error_code="existing_instances",
            message=str(exception),
            status_code=400,
        ) from exception

    _commit_and_push_to_git(f"User: {g.user.username} deleted process group {process_group_id}")
    return Response(json.dumps({"ok": True}), status=200, mimetype="application/json")


def process_group_update(modified_process_group_id: str, body: dict) -> flask.wrappers.Response:
    body_filtered = {
        include_item: body[include_item] for include_item in PROCESS_GROUP_KEYS_TO_UPDATE_FROM_API if include_item in body
    }

    process_group_id = _un_modify_modified_process_model_id(modified_process_group_id)
    if not ProcessModelService.is_process_group_identifier(process_group_id):
        raise ApiError(
            error_code="process_group_does_not_exist",
            message=f"Process Group with given id does not exist: {process_group_id}",
            status_code=400,
        )

    process_group = ProcessGroup(id=process_group_id, **body_filtered)
    ProcessModelService.update_process_group(process_group)

    all_message_models: dict[tuple[str, str], MessageModel] = {}
    MessageDefinitionService.collect_message_models(process_group, process_group_id, all_message_models)
    MessageDefinitionService.delete_message_models_at_location(process_group_id)
    db.session.commit()
    MessageDefinitionService.save_all_message_models(all_message_models)
    db.session.commit()

    _commit_and_push_to_git(f"User: {g.user.username} updated process group {process_group_id}")
    return make_response(jsonify(process_group), 200)


def process_group_list(
    process_group_identifier: str | None = None, page: int = 1, per_page: int = 100
) -> flask.wrappers.Response:
    process_groups = ProcessModelService.get_process_groups_for_api(process_group_identifier)
    batch = ProcessModelService.get_batch(items=process_groups, page=page, per_page=per_page)
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
    return make_response(jsonify(response_json), 200)


# this action is excluded from authorization checks, so it is important that it call:
# AuthorizationService.check_permission_for_request()
# it also allows access to the process group if the user has access to read any of the process models contained in the group
def process_group_show(
    modified_process_group_id: str,
) -> Any:
    process_group_id = _un_modify_modified_process_model_id(modified_process_group_id)
    has_access_to_group_without_considering_subgroups_and_models = True
    try:
        AuthorizationService.check_permission_for_request()
    except NotAuthorizedError:
        has_access_to_group_without_considering_subgroups_and_models = False

    try:
        user = UserService.current_user()
        if (
            has_access_to_group_without_considering_subgroups_and_models
            or AuthorizationService.is_user_allowed_to_view_process_group_with_id(user, process_group_id)
        ):
            # do not return child models and groups here since this call does not check permissions of them
            process_group = ProcessModelService.get_process_group(process_group_id, find_direct_nested_items=False)
        else:
            raise ProcessEntityNotFoundError("viewing this process group is not authorized")
    except ProcessEntityNotFoundError as exception:
        raise (
            ApiError(
                error_code="process_group_cannot_be_found",
                message=f"Process group cannot be found: {process_group_id}",
                status_code=400,
            )
        ) from exception

    process_group.parent_groups = ProcessModelService.get_parent_group_array(process_group.id)
    return make_response(jsonify(process_group), 200)


def process_group_move(modified_process_group_identifier: str, new_location: str) -> flask.wrappers.Response:
    original_process_group_id = _un_modify_modified_process_model_id(modified_process_group_identifier)
    new_process_group = ProcessModelService.process_group_move(original_process_group_id, new_location)
    _commit_and_push_to_git(f"User: {g.user.username} moved process group {original_process_group_id} to {new_process_group.id}")
    return make_response(jsonify(new_process_group), 200)
