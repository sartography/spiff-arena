import flask.wrappers
import json
import requests

from flask import current_app
from flask.wrappers import Response

def connector_proxy_type_ahead_url() -> str:
    """Returns the connector proxy type ahead url."""
    return current_app.config["SPIFFWORKFLOW_BACKEND_CONNECTOR_PROXY_TYPE_AHEAD_URL"]

def type_ahead(category: str, prefix: str, limit: int) -> flask.wrappers.Response:
    # TODO: change url to /type-ahead/{category}
    url = f"{connector_proxy_type_ahead_url()}/{category}?prefix={prefix}&limit={limit}"

    # TODO: try/catch/log etc
    proxy_response = requests.get(url)
    status = proxy_response.status_code
    if status // 100 == 2:
        response = proxy_response.text
    else:
        response = "[]"
    return Response(response, status=status, mimetype="application/json")
