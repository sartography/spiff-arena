from typing import Any
from urllib.parse import urlparse

import requests
from flask import current_app

from spiffworkflow_backend.config import CONNECTOR_PROXY_COMMAND_TIMEOUT


def does(id: str) -> bool:
    return id in _config


def do(id: str, params: dict[str, Any]) -> Any:
    handler = _config[id]["handler"]
    url = params["url"]
    headers = params.get("headers")
    auth = _auth(params)
    data = params.get("data")

    if url.startswith("http://local/"):
        # Use connexion test client directly to route through connexion middleware
        connexion_app = getattr(current_app, 'config', {}).get('CONNEXION_APP')
        if connexion_app and hasattr(connexion_app, 'test_client'):
            try:
                client = connexion_app.test_client()
            except Exception:
                # Fall back to Flask test client if connexion client creation fails
                client = current_app.test_client()
        else:
            client = current_app.test_client()

        # Extract path from URL and prepare parameters for connexion test client
        path = urlparse(url).path
        kwargs = {}

        # Handle headers
        if headers is not None:
            kwargs['headers'] = headers

        # Convert query_string -> params for connexion test client
        query_params = params.get("params")
        if query_params is not None:
            kwargs['params'] = query_params

        return getattr(client, handler)(path, **kwargs)

    return getattr(requests, handler)(  # type: ignore
        url,
        params.get("params"),
        headers=headers,
        auth=auth,
        json=data,
        timeout=CONNECTOR_PROXY_COMMAND_TIMEOUT,
    )


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
    "http/GetRequest": {"params": _ro_params, "handler": "get"},
    "http/HeadRequest": {"params": _ro_params, "handler": "head"},
    "http/PatchRequest": {"params": _rw_params, "handler": "patch"},
    "http/PostRequest": {"params": _rw_params, "handler": "post"},
    "http/PutRequest": {"params": _rw_params, "handler": "put"},
}

commands = [{"id": k, "parameters": v["params"]} for k, v in _config.items()]
