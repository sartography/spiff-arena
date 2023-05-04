import json
import time

import flask.wrappers
from flask import g
from flask import jsonify
from flask import make_response
from flask.wrappers import Response

from spiffworkflow_backend.models.active_user import ActiveUserModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.user import UserModel


def active_user_updates(last_visited_identifier: str) -> Response:
    active_user = ActiveUserModel.query.filter_by(
        user_id=g.user.id, last_visited_identifier=last_visited_identifier
    ).first()
    if active_user is None:
        active_user = ActiveUserModel(
            user_id=g.user.id, last_visited_identifier=last_visited_identifier, last_seen_in_seconds=round(time.time())
        )
        db.session.add(active_user)
        db.session.commit()

    active_user.last_seen_in_seconds = round(time.time())
    db.session.add(active_user)
    db.session.commit()

    cutoff_time_in_seconds = time.time() - 30
    active_users = (
        UserModel.query.join(ActiveUserModel)
        .filter(ActiveUserModel.last_visited_identifier == last_visited_identifier)
        .filter(ActiveUserModel.last_seen_in_seconds > cutoff_time_in_seconds)
        .filter(UserModel.id != g.user.id)
        .all()
    )
    return make_response(jsonify(active_users), 200)


def active_user_unregister(last_visited_identifier: str) -> flask.wrappers.Response:
    active_user = ActiveUserModel.query.filter_by(
        user_id=g.user.id, last_visited_identifier=last_visited_identifier
    ).first()
    if active_user is not None:
        db.session.delete(active_user)
        db.session.commit()

    return Response(json.dumps({"ok": True}), status=200, mimetype="application/json")
