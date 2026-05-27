import json

import requests

from spiffworkflow_backend.connectors.http_connector import _connector_response


def test_connector_response_handles_empty_json_response_body() -> None:
    response = requests.Response()
    response.status_code = 202
    response.headers["Content-Type"] = "application/json"
    response._content = b""

    connector_response = _connector_response(response)

    response_body = json.loads(connector_response.text)
    assert connector_response.status_code == 200
    assert response_body["command_response"]["http_status"] == 202
    assert response_body["command_response"]["body"] == {"raw_response": ""}
    assert response_body["error"] is None
