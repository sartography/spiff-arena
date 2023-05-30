from typing import Any

import flask.wrappers
import requests
from flask import current_app
from flask.wrappers import Response

from spiffworkflow_backend.config import HTTP_REQUEST_TIMEOUT_SECONDS


def connector_proxy_typeahead_url() -> Any:
    """Returns the connector proxy type ahead url."""
    return current_app.config["SPIFFWORKFLOW_BACKEND_CONNECTOR_PROXY_TYPEAHEAD_URL"]


def typeahead(category: str, prefix: str, limit: int) -> flask.wrappers.Response:
    url = f"{connector_proxy_typeahead_url()}/v1/typeahead/{category}?prefix={prefix}&limit={limit}"

    proxy_response = requests.get(url, timeout=HTTP_REQUEST_TIMEOUT_SECONDS)
    status = proxy_response.status_code
    response = proxy_response.text

    return Response(response, status=status, mimetype="application/json")
