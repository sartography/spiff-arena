from flask import make_response
from flask.wrappers import Response
from flask import current_app as app

def enabled() -> Response:
    response = app.config["SCRIPT_ASSIST_ENABLED"]
    return make_response({"ok": response}, 200)

def process_message() -> Response:
    api_key = app.config["SPIFFWORKFLOW_BACKEND_OPENAI_API_KEY"]
    return make_response({"ok": api_key}, 200)
