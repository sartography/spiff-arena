"""APIs for dealing with process groups, process models, and process instances."""
import json
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
import flask.wrappers

from flask.wrappers import Response


def status() -> flask.wrappers.Response:
    """Status."""
    ProcessInstanceModel.query.filter().first()
    return Response(json.dumps({"ok": True}), status=200, mimetype="application/json")
