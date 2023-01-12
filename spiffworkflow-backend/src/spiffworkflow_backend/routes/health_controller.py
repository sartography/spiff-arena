"""APIs for dealing with process groups, process models, and process instances."""
import json

from flask.wrappers import Response

from spiffworkflow_backend.models.process_instance import ProcessInstanceModel


def status() -> Response:
    """Status."""
    ProcessInstanceModel.query.filter().first()
    response = Response(
        json.dumps({"ok": True}), status=200, mimetype="application/json"
    )
    return response
