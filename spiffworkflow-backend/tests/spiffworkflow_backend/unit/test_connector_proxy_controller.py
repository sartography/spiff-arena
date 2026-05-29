from unittest.mock import MagicMock
from unittest.mock import patch

from flask import Flask

from spiffworkflow_backend.routes.connector_proxy_controller import _remote_typeahead
from spiffworkflow_backend.services.connector_proxy_service import connector_proxy_request_proxies


def test_connector_proxy_controller_request_proxies_returns_none_when_not_configured() -> None:
    app = Flask(__name__)
    app.config["SPIFFWORKFLOW_BACKEND_CONNECTOR_PROXY_HTTP_PROXY_URL"] = None

    with app.app_context():
        assert connector_proxy_request_proxies() is None


def test_connector_proxy_controller_request_proxies_returns_http_and_https_proxy() -> None:
    app = Flask(__name__)
    app.config["SPIFFWORKFLOW_BACKEND_CONNECTOR_PROXY_HTTP_PROXY_URL"] = "http://excellent-test-proxy:3128"

    with app.app_context():
        assert connector_proxy_request_proxies() == {
            "http": "http://excellent-test-proxy:3128",
            "https": "http://excellent-test-proxy:3128",
        }


def test_remote_typeahead_uses_connector_proxy_http_proxy_when_configured() -> None:
    app = Flask(__name__)
    app.config["SPIFFWORKFLOW_BACKEND_CONNECTOR_PROXY_TYPEAHEAD_URL"] = "https://pepa.example.com/spiff"
    app.config["SPIFFWORKFLOW_BACKEND_CONNECTOR_PROXY_HTTP_PROXY_URL"] = "http://excellent-test-proxy:3128"
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '["abc"]'

    with app.app_context():
        with patch("spiffworkflow_backend.routes.connector_proxy_controller.safe_requests") as mock_safe_requests:
            mock_safe_requests.get.return_value = mock_response
            response = _remote_typeahead("airport", "a", 3)
            _, call_kwargs = mock_safe_requests.get.call_args

    assert response.status_code == 200
    assert response.get_data(as_text=True) == '["abc"]'
    assert call_kwargs.get("proxies") == {
        "http": "http://excellent-test-proxy:3128",
        "https": "http://excellent-test-proxy:3128",
    }
