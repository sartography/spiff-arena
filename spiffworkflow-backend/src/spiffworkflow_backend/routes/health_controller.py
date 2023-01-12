"""APIs for dealing with process groups, process models, and process instances."""
from flask import make_response
from flask.wrappers import Response

from spiffworkflow_backend.models.process_instance import ProcessInstanceModel


def status() -> Response:
    """Status."""
    ProcessInstanceModel.query.filter().first()
    return make_response({"ok": True}, 200)
