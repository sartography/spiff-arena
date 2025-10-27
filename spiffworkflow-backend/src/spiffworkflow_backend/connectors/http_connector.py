from typing import Any

import requests

from spiffworkflow_backend.config import CONNECTOR_PROXY_COMMAND_TIMEOUT


def does(id: str) -> bool:
    return id in _config


def do(id: str, params: dict[str, Any]) -> Any:
    handler = _config[id]["handler"]
    headers = params.get("headers")
    auth = _auth(params)
    data = params.get("data")

    return handler(  # type: ignore
        params["url"],
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
    "http/DeleteRequest": {"params": _rw_params, "handler": requests.delete},
    "http/GetRequest": {"params": _ro_params, "handler": requests.get},
    "http/HeadRequest": {"params": _ro_params, "handler": requests.head},
    "http/PatchRequest": {"params": _rw_params, "handler": requests.patch},
    "http/PostRequest": {"params": _rw_params, "handler": requests.post},
    "http/PutRequest": {"params": _rw_params, "handler": requests.put},
}

commands = [{"id": k, "parameters": v["params"]} for k, v in _config.items()]
