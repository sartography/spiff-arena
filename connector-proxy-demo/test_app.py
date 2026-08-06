from app import CONNECTOR_PROXY_API_KEY_CONFIG
from app import CONNECTOR_PROXY_API_KEY_HEADER
from app import app


def test_connector_proxy_api_key_is_not_required_when_unconfigured():
    app.config[CONNECTOR_PROXY_API_KEY_CONFIG] = None

    response = app.test_client().get("/v1/commands")

    assert response.status_code != 401


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

    assert response.status_code != 401


def test_connector_proxy_api_key_does_not_block_liveness():
    app.config[CONNECTOR_PROXY_API_KEY_CONFIG] = "expected-api-key"

    response = app.test_client().get("/v1/liveness")

    assert response.status_code != 401
