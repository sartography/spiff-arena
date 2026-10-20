import json
import logging
from pathlib import Path
from unittest.mock import Mock
from unittest.mock import patch

import pytest

from spiffworkflow_backend.services.connector_proxy_response_validator import CALLBACK_REQUEST_SCHEMA
from spiffworkflow_backend.services.connector_proxy_response_validator import CONNECTOR_PROXY_RESPONSE_V2_SCHEMA
from spiffworkflow_backend.services.connector_proxy_response_validator import VALIDATORS
from spiffworkflow_backend.services.connector_proxy_response_validator import warn_on_invalid_connector_proxy_payload

ARENA_ROOT = Path(__file__).resolve().parents[4]
PROTOCOL_PATH = ARENA_ROOT / "connector-proxies/protocol/openapi.json"
LOGGER_NAME = "spiffworkflow_backend.services.connector_proxy_response_validator"


def execution_response(**updates):
    response = {
        "command_response": {
            "body": {"status": "ok"},
            "mimetype": "application/json",
        },
        "command_response_version": 2,
        "error": None,
        "spiff__logs": [],
    }
    response.update(updates)
    return response


def test_backend_schemas_match_openapi_components():
    protocol_schemas = json.loads(PROTOCOL_PATH.read_text())["components"]["schemas"]
    execution_schema = {
        **protocol_schemas["ConnectorProxyResponseV2"],
        "$defs": {
            "ConnectorCommandResponse": protocol_schemas["ConnectorCommandResponse"],
            "ConnectorError": protocol_schemas["ConnectorError"],
        },
    }
    callback_schema = {
        **protocol_schemas["CallbackRequest"],
        "$defs": {
            "ConnectorError": protocol_schemas["ConnectorError"],
        },
    }
    execution_schema["properties"]["command_response"]["$ref"] = "#/$defs/ConnectorCommandResponse"
    execution_schema["properties"]["error"]["oneOf"][0]["$ref"] = "#/$defs/ConnectorError"
    callback_schema["anyOf"][1]["properties"]["error"]["$ref"] = "#/$defs/ConnectorError"

    assert CONNECTOR_PROXY_RESPONSE_V2_SCHEMA == execution_schema
    assert CALLBACK_REQUEST_SCHEMA == callback_schema


@pytest.mark.parametrize(
    ("source", "payload"),
    [
        ("execution", execution_response()),
        (
            "execution",
            execution_response(extension={"value": "accepted"}),
        ),
        (
            "callback",
            {
                "command_response": {"body": {"status": "ok"}},
                "command_response_version": 2,
            },
        ),
        (
            "callback",
            {
                **execution_response(),
                "error": {
                    "error_code": "FAILED",
                    "message": "failed",
                },
            },
        ),
    ],
)
def test_valid_payload_does_not_warn(caplog, source, payload):
    with caplog.at_level(logging.WARNING, logger=LOGGER_NAME):
        warn_on_invalid_connector_proxy_payload(
            payload,
            source=source,
            operator_identifier="example/Example",
        )

    assert not caplog.records


@pytest.mark.parametrize(
    ("source", "payload"),
    [
        (
            "execution",
            execution_response(spiff__logs="not-a-list"),
        ),
        (
            "callback",
            {
                "command_response": {},
                "command_response_version": 2,
            },
        ),
    ],
)
def test_invalid_version_2_payload_warns_without_logging_values(caplog, source, payload):
    payload_marker = "opaque-response-value"
    payload["sensitive_extension"] = payload_marker

    with caplog.at_level(logging.WARNING, logger=LOGGER_NAME):
        warn_on_invalid_connector_proxy_payload(
            payload,
            source=source,
            operator_identifier="example/Example",
        )

    assert len(caplog.records) == 1
    warning = caplog.records[0].getMessage()
    assert "failed schema validation" in warning
    assert f"source={source}" in warning
    assert "operator_identifier=example/Example" in warning
    assert payload_marker not in warning
    assert "sensitive_extension" not in warning


def test_warning_does_not_include_response_data(caplog):
    private_marker = "opaque-token-value"
    payload = execution_response(
        command_response={
            "body": "opaque-body-value",
            "mimetype": "",
            "headers": {"Authorization": "opaque-header-value"},
        },
        spiff__logs=["opaque-connector-log-value"],
    )
    payload["access_token"] = private_marker

    with caplog.at_level(logging.WARNING, logger=LOGGER_NAME):
        warn_on_invalid_connector_proxy_payload(
            payload,
            source="execution",
            operator_identifier="example/Example",
        )

    warning = caplog.records[0].getMessage()
    for private_value in [
        "opaque-body-value",
        "opaque-header-value",
        "opaque-connector-log-value",
        private_marker,
        "Authorization",
        "access_token",
    ]:
        assert private_value not in warning


def test_warning_limits_reported_issues(caplog):
    payload = execution_response(spiff__logs=[None] * 10)

    with caplog.at_level(logging.WARNING, logger=LOGGER_NAME):
        warn_on_invalid_connector_proxy_payload(
            payload,
            source="execution",
            operator_identifier="example/Example",
        )

    _, _, issue_count, issues = caplog.records[0].args
    assert issue_count == 10
    assert len(issues) == 5


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"command_response_version": 1},
        {"command_response_version": 3},
    ],
)
def test_non_version_2_payload_is_not_validated(caplog, payload):
    with caplog.at_level(logging.WARNING, logger=LOGGER_NAME):
        warn_on_invalid_connector_proxy_payload(
            payload,
            source="execution",
            operator_identifier=None,
        )

    assert not caplog.records


def test_validator_failure_is_logged_without_interrupting_processing(caplog):
    exception_marker = "opaque-exception-value"
    failing_validator = Mock()
    failing_validator.iter_errors.side_effect = RuntimeError(exception_marker)
    with (
        patch.dict(VALIDATORS, {"execution": failing_validator}),
        caplog.at_level(logging.ERROR, logger=LOGGER_NAME),
    ):
        warn_on_invalid_connector_proxy_payload(
            execution_response(),
            source="execution",
            operator_identifier="example/Example",
        )

    assert len(caplog.records) == 1
    assert "validation could not run" in caplog.records[0].getMessage()
    assert exception_marker not in caplog.records[0].getMessage()
