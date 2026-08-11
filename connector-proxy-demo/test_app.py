import json
import os
import subprocess
import sys

import pytest

from app import CONNECTOR_PROXY_API_KEY_CONFIG
from app import CONNECTOR_PROXY_API_KEY_HEADER
from app import CONNECTOR_PROXY_CORS_ORIGINS_CONFIG
from app import ConfigurationError
from app import app


def test_connector_proxy_api_key_is_not_required_when_unconfigured():
    app.config[CONNECTOR_PROXY_API_KEY_CONFIG] = None

    response = app.test_client().get("/v1/commands")

    assert response.status_code == 200


def test_connector_proxy_api_key_empty_env_fails_startup():
    env = {**os.environ, CONNECTOR_PROXY_API_KEY_CONFIG: ""}

    result = subprocess.run(
        [sys.executable, "-c", "import app"],
        cwd=os.path.dirname(__file__),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert f"{CONNECTOR_PROXY_API_KEY_CONFIG} config cannot be empty" in result.stderr


def test_connector_proxy_api_key_empty_config_does_not_disable_authentication():
    app.config[CONNECTOR_PROXY_API_KEY_CONFIG] = ""
    previous_testing = app.config.get("TESTING")
    app.config["TESTING"] = True

    try:
        with pytest.raises(ConfigurationError, match=f"{CONNECTOR_PROXY_API_KEY_CONFIG} config cannot be empty"):
            app.test_client().get("/v1/commands")
    finally:
        app.config["TESTING"] = previous_testing


def test_connector_proxy_api_key_is_required_for_command_discovery_when_configured():
    app.config[CONNECTOR_PROXY_API_KEY_CONFIG] = "expected-api-key"

    response = app.test_client().get("/v1/commands")

    assert response.status_code == 401
    assert response.json == {"error": "Unauthorized"}


def test_connector_proxy_api_key_is_required_for_command_execution_when_configured():
    app.config[CONNECTOR_PROXY_API_KEY_CONFIG] = "expected-api-key"

    response = app.test_client().post("/v1/do/example/Example", json={})

    assert response.status_code == 401
    assert response.json == {"error": "Unauthorized"}


def test_connector_proxy_api_key_rejects_wrong_header_value():
    app.config[CONNECTOR_PROXY_API_KEY_CONFIG] = "expected-api-key"

    response = app.test_client().get(
        "/v1/commands",
        headers={CONNECTOR_PROXY_API_KEY_HEADER: "wrong-api-key"},
    )

    assert response.status_code == 401
    assert response.json == {"error": "Unauthorized"}


def test_connector_proxy_api_key_accepts_matching_header_value():
    app.config[CONNECTOR_PROXY_API_KEY_CONFIG] = "expected-api-key"

    response = app.test_client().get(
        "/v1/commands",
        headers={CONNECTOR_PROXY_API_KEY_HEADER: "expected-api-key"},
    )

    assert response.status_code == 200


def test_connector_proxy_api_key_does_not_block_liveness():
    app.config[CONNECTOR_PROXY_API_KEY_CONFIG] = "expected-api-key"

    response = app.test_client().get("/v1/liveness")

    assert response.status_code == 200


def test_connector_proxy_cors_origin_allowlist_and_preflight():
    env = {
        **os.environ,
        CONNECTOR_PROXY_API_KEY_CONFIG: "expected-api-key",
        CONNECTOR_PROXY_CORS_ORIGINS_CONFIG: "https://arena.example.com, http://localhost:7001",
    }
    script = """
import json
from app import app

client = app.test_client()
allowed = client.get('/v1/commands', headers={
    'Origin': 'https://arena.example.com',
    'Spiff-Connector-Proxy-Api-Key': 'expected-api-key',
})
denied = client.get('/v1/commands', headers={
    'Origin': 'https://other.example.com',
    'Spiff-Connector-Proxy-Api-Key': 'expected-api-key',
})
preflight = client.options('/v1/do/example/Example', headers={
    'Origin': 'http://localhost:7001',
    'Access-Control-Request-Method': 'POST',
    'Access-Control-Request-Headers': 'Content-Type, Spiff-Connector-Proxy-Api-Key',
})
print(json.dumps({
    'allowed_origin': allowed.headers.get('Access-Control-Allow-Origin'),
    'denied_origin': denied.headers.get('Access-Control-Allow-Origin'),
    'preflight_status': preflight.status_code,
    'preflight_origin': preflight.headers.get('Access-Control-Allow-Origin'),
    'preflight_headers': preflight.headers.get('Access-Control-Allow-Headers'),
}))
"""

    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=os.path.dirname(__file__),
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    cors_result = json.loads(result.stdout)

    assert cors_result["allowed_origin"] == "https://arena.example.com"
    assert cors_result["denied_origin"] is None
    assert cors_result["preflight_status"] == 200
    assert cors_result["preflight_origin"] == "http://localhost:7001"
    assert CONNECTOR_PROXY_API_KEY_HEADER in cors_result["preflight_headers"]
