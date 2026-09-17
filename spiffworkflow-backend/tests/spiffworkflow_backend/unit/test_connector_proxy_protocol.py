import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from spiffworkflow_backend.connectors import http_connector

ARENA_ROOT = Path(__file__).resolve().parents[4]
PROTOCOL_PATH = ARENA_ROOT / "connector-proxies/protocol/openapi.json"
AGGREGATE_COMMANDS_PATH = ARENA_ROOT / "connector-proxies/aggregate/static/standard/v1/commands.json"


def load_protocol() -> dict[str, Any]:
    return json.loads(PROTOCOL_PATH.read_text())


def protocol_validator(schema_name: str) -> Draft202012Validator:
    protocol = load_protocol()
    protocol["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    protocol["$ref"] = f"#/components/schemas/{schema_name}"
    return Draft202012Validator(protocol)


def test_protocol_component_schemas_are_valid_json_schema():
    for name, schema in load_protocol()["components"]["schemas"].items():
        try:
            Draft202012Validator.check_schema(schema)
        except Exception as exception:
            exception.add_note(f"Invalid protocol component schema: {name}")
            raise


def test_maintained_command_catalogs_match_protocol():
    embedded_catalog = http_connector.commands
    aggregate_catalog = json.loads(AGGREGATE_COMMANDS_PATH.read_text())
    validator = protocol_validator("CommandCatalog")

    validator.validate(embedded_catalog)
    validator.validate(aggregate_catalog)


def test_embedded_http_connector_response_matches_protocol():
    class UpstreamResponse:
        status_code = 200
        text = '{"status": "ok"}'
        headers = {"Content-Type": "application/json"}

    response = http_connector._connector_response(UpstreamResponse(), include_response_headers=True)  # type: ignore[arg-type]

    assert response.status_code == 200
    protocol_validator("ConnectorProxyResponseV2").validate(json.loads(response.text))


def test_openapi_examples_match_protocol_schemas():
    protocol = load_protocol()
    paths = protocol["paths"]
    component_examples = [
        ("CommandCatalog", paths["/v1/commands"]["get"]["responses"]["200"]["content"]["application/json"]["example"]),
        (
            "ConnectorProxyResponseV2",
            paths["/v1/do/{connector}/{command}"]["post"]["responses"]["200"]["content"]["application/json"]["example"],
        ),
    ]
    callback = paths["/v1/do/{connector}/{command}"]["post"]["callbacks"]["commandCompleted"]
    callback_operation = callback["{$request.body#/spiff__callback_url}"]["put"]
    component_examples.append(
        (
            "ConnectorProxyResponseV2",
            callback_operation["requestBody"]["content"]["application/json"]["example"],
        )
    )
    for schema_name, example in component_examples:
        protocol_validator(schema_name).validate(example)
