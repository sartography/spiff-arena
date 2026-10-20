import logging
from typing import Any
from typing import Literal

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

logger = logging.getLogger(__name__)

PayloadSource = Literal["execution", "callback"]
MAX_LOGGED_ISSUES = 5

CONNECTOR_PROXY_RESPONSE_V2_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": [
        "command_response",
        "command_response_version",
        "error",
        "spiff__logs",
    ],
    "properties": {
        "command_response": {
            "$ref": "#/$defs/ConnectorCommandResponse",
        },
        "command_response_version": {
            "const": 2,
        },
        "error": {
            "oneOf": [
                {
                    "$ref": "#/$defs/ConnectorError",
                },
                {
                    "type": "null",
                },
            ],
        },
        "spiff__logs": {
            "type": "array",
            "items": {
                "type": "string",
            },
        },
    },
    "additionalProperties": True,
    "$defs": {
        "ConnectorCommandResponse": {
            "type": "object",
            "required": [
                "body",
                "mimetype",
            ],
            "properties": {
                "body": True,
                "mimetype": {
                    "type": "string",
                    "minLength": 1,
                },
                "http_status": {
                    "type": "integer",
                    "minimum": 100,
                    "maximum": 599,
                },
                "headers": {
                    "type": "object",
                    "additionalProperties": True,
                },
            },
            "additionalProperties": True,
        },
        "ConnectorError": {
            "type": "object",
            "required": [
                "error_code",
                "message",
            ],
            "properties": {
                "error_code": {
                    "type": "string",
                    "minLength": 1,
                },
                "message": {
                    "type": "string",
                },
            },
            "additionalProperties": True,
        },
    },
}

CALLBACK_REQUEST_SCHEMA: dict[str, Any] = {
    "anyOf": [
        {
            "type": "object",
            "required": [
                "command_response",
            ],
            "properties": {
                "command_response": {
                    "type": "object",
                    "required": [
                        "body",
                    ],
                    "properties": {
                        "body": True,
                    },
                    "additionalProperties": True,
                },
            },
            "additionalProperties": True,
        },
        {
            "type": "object",
            "required": [
                "error",
            ],
            "properties": {
                "error": {
                    "$ref": "#/$defs/ConnectorError",
                },
            },
            "additionalProperties": True,
        },
    ],
    "$defs": {
        "ConnectorError": CONNECTOR_PROXY_RESPONSE_V2_SCHEMA["$defs"]["ConnectorError"],
    },
}

VALIDATORS = {
    "execution": Draft202012Validator(CONNECTOR_PROXY_RESPONSE_V2_SCHEMA),
    "callback": Draft202012Validator(CALLBACK_REQUEST_SCHEMA),
}


def warn_on_invalid_connector_proxy_payload(
    payload: Any,
    *,
    source: PayloadSource,
    operator_identifier: str | None,
) -> None:
    if not isinstance(payload, dict) or payload.get("command_response_version") != 2:
        return

    try:
        issue_count = 0
        issues: list[str] = []
        for error in VALIDATORS[source].iter_errors(payload):
            issue_count += 1
            if len(issues) < MAX_LOGGED_ISSUES:
                issues.append(_validation_issue(error))
    except Exception:
        logger.error(
            "Connector proxy version 2 schema validation could not run: source=%s operator_identifier=%s",
            source,
            operator_identifier or "<unknown>",
        )
        return

    if not issue_count:
        return

    logger.warning(
        "Connector proxy version 2 payload failed schema validation: "
        "source=%s operator_identifier=%s issue_count=%d issues=%s",
        source,
        operator_identifier or "<unknown>",
        issue_count,
        issues,
    )


def _validation_issue(error: ValidationError) -> str:
    path = ".".join(str(part) for part in error.absolute_path) or "<root>"
    return f"{path}:{error.validator}"
