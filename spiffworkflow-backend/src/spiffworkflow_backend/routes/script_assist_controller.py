from flask import make_response
from flask.wrappers import Response
from flask import current_app as app

from spiffworkflow_backend.models.process_instance import ProcessInstanceModel

def enabled() -> Response:
    ProcessInstanceModel.query.filter().first()
    response = app.config["SCRIPT_ASSIST_ENABLED"]
    return make_response({"enabled": response}, 200)

def script_message() -> Response:
    ProcessInstanceModel.query.filter().first()
    api_key = app.config["SPIFFWORKFLOW_BACKEND_OPENAI_API_KEY"]
    return make_response({"enabled": api_key}, 200)
