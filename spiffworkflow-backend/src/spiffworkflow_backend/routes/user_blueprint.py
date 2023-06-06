import json
from typing import Any
from typing import Final

import flask.wrappers
from flask import Blueprint
from flask import Response
from flask import request
from sqlalchemy.exc import IntegrityError

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.models.user_group_assignment import UserGroupAssignmentModel

APPLICATION_JSON: Final = "application/json"

user_blueprint = Blueprint("main", __name__)


# @user_blueprint.route("/user/<username>", methods=["GET"])
# def create_user(username: str) -> flask.wrappers.Response:
#     """Create_user."""
#     user = UserService.create_user('internal', username)
#     return Response(json.dumps({"id": user.id}), status=201, mimetype=APPLICATION_JSON)


# def _create_user(username):
#     user = UserModel.query.filter_by(username=username).first()
#     if user is not None:
#         raise (
#             ApiError(
#                 error_code="user_already_exists",
#                 message=f"User already exists: {username}",
#                 status_code=409,
#             )
#         )
#
#     user = UserModel(username=username,
#                      service='internal',
#                      service_id=username,
#                      name=username)
#     try:
#         db.session.add(user)
#     except IntegrityError as exception:
#         raise (
#             ApiError(error_code="integrity_error", message=repr(exception), status_code=500)
#         ) from exception
#
#     try:
#         db.session.commit()
#     except Exception as e:
#         db.session.rollback()
#         raise ApiError(code='add_user_error',
#                        message=f'Could not add user {username}') from e
#     try:
#         create_principal(user.id)
#     except ApiError as ae:
#         # TODO: What is the right way to do this
#         raise ae
#     return user
#
@user_blueprint.route("/user/<username>", methods=["DELETE"])
def delete_user(username: str) -> flask.wrappers.Response:
    user = UserModel.query.filter_by(username=username).first()
    if user is None:
        raise (
            ApiError(
                error_code="user_cannot_be_found",
                message=f"User cannot be found: {username}",
                status_code=400,
            )
        )

    db.session.delete(user)
    db.session.commit()

    return Response(json.dumps({"ok": True}), status=204, mimetype=APPLICATION_JSON)


@user_blueprint.route("/group/<group_name>", methods=["GET"])
def create_group(group_name: str) -> flask.wrappers.Response:
    group = GroupModel.query.filter_by(name=group_name).first()
    if group is not None:
        raise (
            ApiError(
                error_code="group_already_exists",
                message=f"Group already exists: {group_name}",
                status_code=409,
            )
        )

    group = GroupModel(name=group_name)
    try:
        db.session.add(group)
    except IntegrityError as exception:
        raise (ApiError(error_code="integrity_error", message=repr(exception), status_code=500)) from exception
    db.session.commit()

    return Response(json.dumps({"id": group.id}), status=201, mimetype=APPLICATION_JSON)


@user_blueprint.route("/group/<group_name>", methods=["DELETE"])
def delete_group(group_name: str) -> flask.wrappers.Response:
    group = GroupModel.query.filter_by(name=group_name).first()
    if group is None:
        raise (
            ApiError(
                error_code="group_cannot_be_found",
                message=f"Group cannot be found: {group_name}",
                status_code=400,
            )
        )

    db.session.delete(group)
    db.session.commit()

    return Response(json.dumps({"ok": True}), status=204, mimetype=APPLICATION_JSON)


@user_blueprint.route("/assign_user_to_group", methods=["POST"])
def assign_user_to_group() -> flask.wrappers.Response:
    user = get_user_from_request()
    group = get_group_from_request()

    user_group_assignment = UserGroupAssignmentModel.query.filter_by(user_id=user.id, group_id=group.id).first()
    if user_group_assignment is not None:
        raise (
            ApiError(
                error_code="user_is_already_in_group",
                message=f"User ({user.id}) is already in group ({group.id})",
                status_code=409,
            )
        )

    user_group_assignment = UserGroupAssignmentModel(user_id=user.id, group_id=group.id)
    db.session.add(user_group_assignment)
    db.session.commit()

    return Response(
        json.dumps({"id": user_group_assignment.id}),
        status=201,
        mimetype=APPLICATION_JSON,
    )


@user_blueprint.route("/remove_user_from_group", methods=["POST"])
def remove_user_from_group() -> flask.wrappers.Response:
    user = get_user_from_request()
    group = get_group_from_request()

    user_group_assignment = UserGroupAssignmentModel.query.filter_by(user_id=user.id, group_id=group.id).first()
    if user_group_assignment is None:
        raise (
            ApiError(
                error_code="user_not_in_group",
                message=f"User ({user.id}) is not in group ({group.id})",
                status_code=400,
            )
        )

    db.session.delete(user_group_assignment)
    db.session.commit()

    return Response(
        json.dumps({"ok": True}),
        status=204,
        mimetype=APPLICATION_JSON,
    )


def get_value_from_request_json(key: str) -> Any:
    if request.json is None:
        return None
    return request.json.get(key)


def get_user_from_request() -> Any:
    user_id = get_value_from_request_json("user_id")

    if user_id is None:
        raise (
            ApiError(
                error_code="user_id_is_required",
                message="Attribute user_id is required",
                status_code=400,
            )
        )

    user = UserModel.query.filter_by(id=user_id).first()
    if user is None:
        raise (
            ApiError(
                error_code="user_cannot_be_found",
                message=f"User cannot be found: {user_id}",
                status_code=400,
            )
        )
    return user


def get_group_from_request() -> Any:
    group_id = get_value_from_request_json("group_id")

    if group_id is None:
        raise (
            ApiError(
                error_code="group_id_is_required",
                message="Attribute group_id is required",
                status_code=400,
            )
        )

    group = GroupModel.query.filter_by(id=group_id).first()
    if group is None:
        raise (
            ApiError(
                error_code="group_cannot_be_found",
                message=f"Group cannot be found: {group_id}",
                status_code=400,
            )
        )
    return group
