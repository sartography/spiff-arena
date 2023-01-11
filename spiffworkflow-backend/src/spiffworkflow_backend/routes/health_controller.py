"""APIs for dealing with process groups, process models, and process instances."""
import json

import flask.wrappers
from flask.wrappers import Response

from spiffworkflow_backend.models.process_instance import ProcessInstanceModel


def status() -> flask.wrappers.Response:
    """Status."""
    ProcessInstanceModel.query.filter().first()
    response = Response(json.dumps({"ok": True}), status=200, mimetype="application/json")
    response.set_cookie('TEST_COOKIE', 'HEY')
    response.set_cookie('TEST_COOKIE', 'HEY', domain='spiff.localdev')
    return response
