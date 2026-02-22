import json
from typing import Any
from typing import cast
from urllib.parse import urlparse

import requests
from flask import current_app

from spiffworkflow_backend.config import CONNECTOR_PROXY_COMMAND_TIMEOUT


class HttpConnectorResponse:
    text: str | None = None
    status_code: int | None = None


def does(id: str) -> bool:
    return id in _config


def do(id: str, params: dict[str, Any]) -> Any:
    handler = cast(str, _config[id]["handler"])
    url = params["url"]
    headers = params.get("headers")
    auth = _auth(params)
    data = params.get("data")

    if url.startswith("http://local/"):
        # Use connexion test client directly to route through connexion middleware
        connexion_app = getattr(current_app, "config", {}).get("CONNEXION_APP")
        if connexion_app and hasattr(connexion_app, "test_client"):
            client = connexion_app.test_client()
        else:
            raise ValueError("CONNEXION_APP not available or does not have test_client method")

        # Extract path from URL and prepare parameters for connexion test client
        path = urlparse(url).path
        kwargs = {}

        # Handle headers
        if headers is not None:
            kwargs["headers"] = headers

        # Convert query_string -> params for connexion test client
        query_params = params.get("params")
        if query_params is not None:
            kwargs["params"] = query_params

        # Handle request body - check if data should be treated as JSON
        if data is not None:
            # If data is a dict or list, treat it as JSON (matching requests semantics)
            if isinstance(data, dict | list):
                kwargs["json"] = data
            else:
                # Otherwise treat as raw data
                kwargs["data"] = data

        # Handle authentication
        if auth is not None:
            # Convert (user, pass) tuple to Authorization header for test client
            import base64

            username, password = auth
            credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
            if "headers" not in kwargs:
                kwargs["headers"] = {}
            kwargs["headers"]["Authorization"] = f"Basic {credentials}"

        response = getattr(client, handler)(path, **kwargs)

    else:
        response = getattr(requests, handler)(
            url,
            params.get("params"),
            headers=headers,
            auth=auth,
            json=data,
            timeout=CONNECTOR_PROXY_COMMAND_TIMEOUT,
        )
    return _connector_response(response)


def _connector_response(http_response: requests.Response) -> HttpConnectorResponse:
    status = http_response.status_code

    content_type = http_response.headers.get("Content-Type", "")
    raw_response = http_response.text

    if "application/json" in content_type:
        command_response = json.loads(raw_response)
    else:
        command_response = {"raw_response": raw_response}

    return_dict = {
        "command_response": {
            "body": command_response,
            "mimetype": "application/json",
            "http_status": status,
        },
        "command_response_version": 2,
        "error": None,
        "spiff__logs": [],
    }

    # create a blank object so we can mimic an actual http response object
    obj = HttpConnectorResponse()
    obj.text = json.dumps(return_dict)
    obj.status_code = http_response.status_code
    return obj


def _auth(params: dict[str, Any]) -> tuple[str, str] | None:
    username = params.get("basic_auth_username")
    password = params.get("basic_auth_password")

    return (username, password) if username and password else None


_base_params = [
    {"id": "url", "type": "str", "required": True},
    {"id": "headers", "type": "any", "required": False},
]

_basic_auth_params = [
    {"id": "basic_auth_username", "type": "str", "required": False},
    {"id": "basic_auth_password", "type": "str", "required": False},
]

_ro_params = [
    *_base_params,
    {"id": "params", "type": "any", "required": False},
    *_basic_auth_params,
]

_rw_params = [
    *_base_params,
    {"id": "data", "type": "any", "required": False},
    *_basic_auth_params,
]

_config = {
    "http/DeleteRequest": {"params": _rw_params, "handler": "delete"},
    "http/DeleteRequestV2": {"params": _rw_params, "handler": "delete"},
    "http/GetRequest": {"params": _ro_params, "handler": "get"},
    "http/GetRequestV2": {"params": _ro_params, "handler": "get"},
    "http/HeadRequest": {"params": _ro_params, "handler": "head"},
    "http/HeadRequestV2": {"params": _ro_params, "handler": "head"},
    "http/PatchRequest": {"params": _rw_params, "handler": "patch"},
    "http/PatchRequestV2": {"params": _rw_params, "handler": "patch"},
    "http/PostRequest": {"params": _rw_params, "handler": "post"},
    "http/PostRequestV2": {"params": _rw_params, "handler": "post"},
    "http/PutRequest": {"params": _rw_params, "handler": "put"},
    "http/PutRequestV2": {"params": _rw_params, "handler": "put"},
}

commands = [{"id": k, "parameters": v["params"]} for k, v in _config.items()]
