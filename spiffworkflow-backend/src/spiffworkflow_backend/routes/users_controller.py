"""Users_controller."""
import flask
from flask import current_app
from flask import g
from flask import jsonify
from flask import make_response

from spiffworkflow_backend.models.user import UserModel


def user_search(username_prefix: str) -> flask.wrappers.Response:
    """User_search."""
    found_users = UserModel.query.filter(UserModel.username.like(f"{username_prefix}%")).all()  # type: ignore

    response_json = {
        "users": found_users,
        "username_prefix": username_prefix,
    }
    return make_response(jsonify(response_json), 200)


def user_group_list_for_current_user() -> flask.wrappers.Response:
    """User_group_list_for_current_user."""
    groups = g.user.groups
    # TODO: filter out the default group and have a way to know what is the default group
    group_identifiers = [
        i.identifier
        for i in groups
        if i.identifier != current_app.config["SPIFFWORKFLOW_DEFAULT_USER_GROUP"]
    ]
    return make_response(jsonify(sorted(group_identifiers)), 200)
