import json
import time
from typing import Generator

import flask.wrappers
from flask import current_app
from flask import g
from flask import stream_with_context
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

    return Response(
        stream_with_context(_active_user_updates(last_visited_identifier, active_user=active_user)),
        mimetype="text/event-stream",
        headers={"X-Accel-Buffering": "no"},
    )


def _active_user_updates(last_visited_identifier: str, active_user: ActiveUserModel) -> Generator[str, None, None]:
    while True:
        active_user.last_seen_in_seconds = round(time.time())
        db.session.add(active_user)
        db.session.commit()

        cutoff_time_in_seconds = time.time() - 15
        active_users = (
            UserModel.query.join(ActiveUserModel)
            .filter(ActiveUserModel.last_visited_identifier == last_visited_identifier)
            .filter(ActiveUserModel.last_seen_in_seconds > cutoff_time_in_seconds)
            .filter(UserModel.id != g.user.id)
            .all()
        )
        yield f"data: {current_app.json.dumps(active_users)} \n\n"

        time.sleep(5)


def active_user_unregister(last_visited_identifier: str) -> flask.wrappers.Response:
    active_user = ActiveUserModel.query.filter_by(
        user_id=g.user.id, last_visited_identifier=last_visited_identifier
    ).first()
    if active_user is not None:
        db.session.delete(active_user)
        db.session.commit()

    return Response(json.dumps({"ok": True}), status=200, mimetype="application/json")
