from flask import make_response
from flask.wrappers import Response
from flask import current_app as app

from spiffworkflow_backend.models.process_instance import ProcessInstanceModel

def status() -> Response:
    ProcessInstanceModel.query.filter().first()
    response = app.config["SCRIPT_ASSIST_ENABLED"]
    return make_response({"enabled": response}, 200)
