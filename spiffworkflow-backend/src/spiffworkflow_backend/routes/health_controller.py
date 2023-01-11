"""APIs for dealing with process groups, process models, and process instances."""
import json
from flask import current_app

import flask.wrappers
from flask.wrappers import Response

from spiffworkflow_backend.models.process_instance import ProcessInstanceModel


def status() -> flask.wrappers.Response:
    """Status."""
    ProcessInstanceModel.query.filter().first()
    response = Response(json.dumps({"ok": True}), status=200, mimetype="application/json")
    # print(f"current_app.config.get('SPIFFWORKFLOW_FRONTEND_URL').replace('http://', ''): {current_app.config.get('SPIFFWORKFLOW_FRONTEND_URL').replace('http://', '')}")
    response.set_cookie('TEST_COOKIE1', 'HEY', domain=None)
    return response
