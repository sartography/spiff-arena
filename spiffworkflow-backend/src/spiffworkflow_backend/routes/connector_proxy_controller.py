from typing import Any

import flask.wrappers
import requests
from flask import current_app
from flask.wrappers import Response


def connector_proxy_type_ahead_url() -> Any:
    """Returns the connector proxy type ahead url."""
    return current_app.config["SPIFFWORKFLOW_BACKEND_CONNECTOR_PROXY_TYPE_AHEAD_URL"]


def type_ahead(category: str, prefix: str, limit: int) -> flask.wrappers.Response:
    url = f"{connector_proxy_type_ahead_url()}/v1/type-ahead/{category}?prefix={prefix}&limit={limit}"

    proxy_response = requests.get(url)
    status = proxy_response.status_code
    if status // 100 == 2:
        response = proxy_response.text
    else:
        # supress pop up errors on the client
        status = 200
        response = "[]"
    return Response(response, status=status, mimetype="application/json")
