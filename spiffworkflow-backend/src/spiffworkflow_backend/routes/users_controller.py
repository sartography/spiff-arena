from typing import Any

import flask
from flask import current_app
from flask import g
from flask import jsonify
from flask import make_response

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.user import UserModel


def user_exists_by_username(body: dict[str, Any]) -> flask.wrappers.Response:
    if "username" not in body:
        raise ApiError(
            error_code="username_not_given",
            message="Username could not be found in post body.",
            status_code=400,
        )
    username = body["username"]
    found_user = UserModel.query.filter_by(username=username).first()
    return make_response(jsonify({"user_found": found_user is not None}), 200)


def user_search(username_prefix: str) -> flask.wrappers.Response:
    found_users = UserModel.query.filter(UserModel.username.like(f"{username_prefix}%")).all()  # type: ignore

    response_json = {
        "users": found_users,
        "username_prefix": username_prefix,
    }
    return make_response(jsonify(response_json), 200)


def user_group_list_for_current_user() -> flask.wrappers.Response:
    groups = g.user.groups
    # TODO: filter out the default group and have a way to know what is the default group
    group_identifiers = [
        i.identifier for i in groups if i.identifier != current_app.config["SPIFFWORKFLOW_BACKEND_DEFAULT_USER_GROUP"]
    ]
    return make_response(jsonify(sorted(group_identifiers)), 200)


def users_in_group(group_name: str) -> flask.wrappers.Response:
    group = GroupModel.query.filter_by(identifier=group_name).first()

    if group is None:
        return make_response(jsonify([]), 200)

    users = (
        db.session.query(
            UserModel.id,
            UserModel.username,
            UserModel.email,
            UserModel.display_name,
        )
        .join(GroupModel.users)  # type: ignore[no-untyped-call]
        .filter(GroupModel.identifier == group_name)
        .all()
    )

    return make_response(jsonify(users), 200)
