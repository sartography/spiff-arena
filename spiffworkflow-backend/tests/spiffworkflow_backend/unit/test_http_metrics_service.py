import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from connexion import FlaskApp
from connexion.lifecycle import ConnexionRequest
from connexion.lifecycle import ConnexionResponse
from connexion.resolver import Resolver
from prometheus_client import CollectorRegistry
from prometheus_client import Gauge
from starlette.testclient import TestClient

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.services.monitoring_service import setup_prometheus_metrics


@pytest.mark.parametrize("status", [200, 400, 401, 403, 404, 409, 500, 503])
@pytest.mark.parametrize("raises", [False, True])
def test_http_metrics_use_final_response_status(status: int, raises: bool) -> None:
    app = FlaskApp(__name__)
    registry = CollectorRegistry()
    setup_prometheus_metrics(app, registry=registry)

    def test_endpoint() -> Any:
        if raises:
            raise ApiError(error_code="test_error", message="Test error", status_code=status)
        return "response", status

    app.app.add_url_rule("/test", view_func=test_endpoint)

    # Match Arena's catch-all handler registration, not a Flask error handler.
    def handle_error(request: ConnexionRequest, exception: Exception) -> ConnexionResponse:
        assert isinstance(exception, ApiError)
        return ConnexionResponse(status_code=exception.status_code, body="error", mimetype="text/plain")

    app.add_error_handler(Exception, handle_error)
    with TestClient(app) as client:
        assert client.get("/test").status_code == status
        assert client.get("/metrics").status_code == 200

    labels = {"method": "GET", "status": str(status)}
    assert registry.get_sample_value("flask_http_request_total", labels) == 1
    assert registry.get_sample_value("flask_http_request_duration_seconds_count", {**labels, "endpoint": "test_endpoint"}) == 1
    assert registry.get_sample_value("flask_http_request_exceptions_total", labels) == (1 if raises else None)
    totals = [sample for metric in registry.collect() for sample in metric.samples if sample.name == "flask_http_request_total"]
    assert len(totals) == 1  # No phantom 500s or /metrics self-counting.


def test_unexpected_exception_is_counted_as_500() -> None:
    app = FlaskApp(__name__)
    registry = CollectorRegistry()
    setup_prometheus_metrics(app, registry=registry)

    def failing_endpoint() -> None:
        raise RuntimeError("Unexpected failure")

    app.app.add_url_rule("/failure", view_func=failing_endpoint)
    with TestClient(app) as client:
        assert client.get("/failure").status_code == 500
    labels = {"method": "GET", "status": "500"}
    assert registry.get_sample_value("flask_http_request_total", labels) == 1
    assert registry.get_sample_value("flask_http_request_exceptions_total", labels) == 1


def test_unmatched_route_is_counted_as_404() -> None:
    app = FlaskApp(__name__)
    registry = CollectorRegistry()
    setup_prometheus_metrics(app, registry=registry)
    with TestClient(app) as client:
        assert client.get("/missing").status_code == 404
    assert registry.get_sample_value("flask_http_request_total", {"method": "GET", "status": "404"}) == 1
    assert registry.get_sample_value("flask_http_request_total", {"method": "GET", "status": "500"}) is None


def test_connexion_validation_error_is_counted_as_400() -> None:
    app = FlaskApp(__name__)
    registry = CollectorRegistry()
    setup_prometheus_metrics(app, registry=registry)
    app.add_api(
        {
            "openapi": "3.0.0",
            "info": {"title": "Metrics test", "version": "1"},
            "paths": {
                "/validated": {
                    "get": {
                        "operationId": "validated",
                        "parameters": [{"name": "count", "in": "query", "required": True, "schema": {"type": "integer"}}],
                        "responses": {"200": {"description": "OK"}},
                    }
                }
            },
        },
        resolver=Resolver(lambda operation_id: lambda count: "ok"),
    )
    with TestClient(app) as client:
        assert client.get("/validated?count=invalid").status_code == 400
        assert client.get("/validated?count=1").status_code == 200
    assert registry.get_sample_value("flask_http_request_total", {"method": "GET", "status": "400"}) == 1
    assert registry.get_sample_value("flask_http_request_total", {"method": "GET", "status": "200"}) == 1
    assert registry.get_sample_value("flask_http_request_total", {"method": "GET", "status": "500"}) is None


@pytest.mark.parametrize("version_data", [None, {}, {"org.opencontainers.image.version": "test-version"}])
def test_version_info_registration(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, version_data: dict[str, str] | None) -> None:
    monkeypatch.chdir(tmp_path)
    if version_data is not None:
        (tmp_path / "version_info.json").write_text(json.dumps(version_data))
    registry = CollectorRegistry()
    for _ in range(2):
        setup_prometheus_metrics(FlaskApp(__name__), registry=registry)
    assert registry.get_sample_value("version_info", {"org_opencontainers_image_version": "test-version"}) == (
        1 if version_data else None
    )


def test_existing_version_info_gauge_is_reused() -> None:
    registry = CollectorRegistry()
    gauge = Gauge("version_info", "Existing version", ("revision",), registry=registry)
    gauge.labels(revision="existing").set(1)
    with patch("spiffworkflow_backend.services.monitoring_service.get_version_info_data") as read_version:
        setup_prometheus_metrics(FlaskApp(__name__), registry=registry)
        read_version.assert_not_called()
    assert registry.get_sample_value("version_info", {"revision": "existing"}) == 1
    gauge.labels(revision="existing").set(2)
    assert registry.get_sample_value("version_info", {"revision": "existing"}) == 2


def test_multiple_apps_can_share_registry() -> None:
    registry = CollectorRegistry()
    for _ in range(2):
        app = FlaskApp(__name__)
        setup_prometheus_metrics(app, registry=registry)
        with TestClient(app) as client:
            assert client.get("/missing").status_code == 404
    assert registry.get_sample_value("flask_http_request_total", {"method": "GET", "status": "404"}) == 2
