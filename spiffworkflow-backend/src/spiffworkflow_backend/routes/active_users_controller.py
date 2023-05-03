import json
import os
import time
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.models.db import db
from typing import Generator
from flask import stream_with_context
import re
from typing import Any
from typing import Dict
from typing import Optional
from typing import Union

import connexion  # type: ignore
import flask.wrappers
from flask import current_app
from flask import g
from flask import jsonify
from flask import make_response
from flask.wrappers import Response
from spiffworkflow_backend.models.active_user import ActiveUserModel
from werkzeug.datastructures import FileStorage


def active_user_updates(last_visited_identifier: str) -> Response:
    active_user = ActiveUserModel.query.filter_by(user_id=g.user.id, last_visited_identifier=last_visited_identifier).first()
    if active_user is None:
        active_user = ActiveUserModel(user_id=g.user.id, last_visited_identifier=last_visited_identifier)
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

        time.sleep(1)
        cutoff_time_in_seconds = time.time() - 7
        active_users = (
            UserModel.query
            .join(ActiveUserModel)
            .filter(ActiveUserModel.last_visited_identifier == last_visited_identifier)
            .filter(ActiveUserModel.last_seen_in_seconds > cutoff_time_in_seconds)
            # .filter(UserModel.id != g.user.id)
            .all()
        )
        yield f"data: {current_app.json.dumps(active_users)} \n\n"


def active_user_unregister(
    last_visited_identifier: str
) -> flask.wrappers.Response:
    active_user = ActiveUserModel.query.filter_by(user_id=g.user.id, last_visited_identifier=last_visited_identifier).first()
    if active_user is not None:
        db.session.delete(active_user)
        db.session.commit()

    return Response(json.dumps({"ok": True}), status=200, mimetype="application/json")
