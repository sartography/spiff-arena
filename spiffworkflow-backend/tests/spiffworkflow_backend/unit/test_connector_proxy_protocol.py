import ast
import json
import re
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from spiffworkflow_backend.connectors import http_connector

ARENA_ROOT = Path(__file__).resolve().parents[4]
PROTOCOL_PATH = ARENA_ROOT / "connector-proxies/protocol/openapi.json"
ASYNC_HTTP_MAIN_PATH = ARENA_ROOT / "connector-proxies/async-http/main.py"
AGGREGATE_COMMANDS_PATH = ARENA_ROOT / "connector-proxies/aggregate/static/standard/v1/commands.json"
AGGREGATE_NGINX_PATH = ARENA_ROOT / "connector-proxies/aggregate/nginx/conf.d/default.conf"
DEMO_EXAMPLE_PATH = (
    ARENA_ROOT / "connector-proxy-demo/connector-example/src/connector_example/commands/example.py"
)


def load_protocol() -> dict[str, Any]:
    return json.loads(PROTOCOL_PATH.read_text())


def protocol_validator(schema_name: str) -> Draft202012Validator:
    protocol = load_protocol()
    protocol["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    protocol["$ref"] = f"#/components/schemas/{schema_name}"
    return Draft202012Validator(protocol)


def load_async_http_catalog() -> list[dict[str, Any]]:
    module = ast.parse(ASYNC_HTTP_MAIN_PATH.read_text())
    namespace: dict[str, Any] = {}
    for statement in module.body:
        if (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
        ):
            try:
                namespace[statement.targets[0].id] = static_value(statement.value, namespace)
            except (KeyError, TypeError):
                continue
    return namespace["embedded_connectors"]


def static_value(node: ast.expr, namespace: dict[str, Any]) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return namespace[node.id]
    if isinstance(node, ast.List):
        values = []
        for item in node.elts:
            if isinstance(item, ast.Starred):
                values.extend(static_value(item.value, namespace))
            else:
                values.append(static_value(item, namespace))
        return values
    if isinstance(node, ast.Dict):
        return {
            static_value(key, namespace): static_value(value, namespace)
            for key, value in zip(node.keys, node.values, strict=True)
        }
    raise TypeError(f"Unsupported static expression: {type(node).__name__}")


def assigned_dict(method: ast.FunctionDef, variable_name: str) -> ast.Dict:
    for statement in method.body:
        if (
            isinstance(statement, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == variable_name for target in statement.targets)
            and isinstance(statement.value, ast.Dict)
        ):
            return statement.value
        if (
            isinstance(statement, ast.AnnAssign)
            and isinstance(statement.target, ast.Name)
            and statement.target.id == variable_name
            and isinstance(statement.value, ast.Dict)
        ):
            return statement.value
    raise AssertionError(f"{variable_name} is not assigned a dictionary")


def dict_keys(node: ast.Dict) -> set[str]:
    return {key.value for key in node.keys if isinstance(key, ast.Constant) and isinstance(key.value, str)}


def test_protocol_component_schemas_are_valid_json_schema():
    for name, schema in load_protocol()["components"]["schemas"].items():
        try:
            Draft202012Validator.check_schema(schema)
        except Exception as exception:
            exception.add_note(f"Invalid protocol component schema: {name}")
            raise


def test_maintained_command_catalogs_match_protocol():
    embedded_catalog = http_connector.commands
    async_http_catalog = load_async_http_catalog()
    aggregate_catalog = json.loads(AGGREGATE_COMMANDS_PATH.read_text())
    validator = protocol_validator("CommandCatalog")

    validator.validate(embedded_catalog)
    validator.validate(async_http_catalog)
    validator.validate(aggregate_catalog)


def test_demo_example_exposes_protocol_shapes():
    module = ast.parse(DEMO_EXAMPLE_PATH.read_text())
    example_class = next(node for node in module.body if isinstance(node, ast.ClassDef) and node.name == "Example")
    init_method = next(
        node for node in example_class.body if isinstance(node, ast.FunctionDef) and node.name == "__init__"
    )
    execute_method = next(
        node for node in example_class.body if isinstance(node, ast.FunctionDef) and node.name == "execute"
    )

    parameters = [
        {"id": argument.arg, "type": argument.annotation.id, "required": True}
        for argument in init_method.args.args
        if argument.arg != "self" and isinstance(argument.annotation, ast.Name)
    ]
    protocol_validator("CommandCatalog").validate([{"id": "example/Example", "parameters": parameters}])

    assert dict_keys(assigned_dict(execute_method, "return_response")) >= {"body", "mimetype"}
    assert dict_keys(assigned_dict(execute_method, "result")) >= {
        "command_response",
        "command_response_version",
        "error",
        "spiff__logs",
    }


def test_async_http_execution_routes_match_advertised_commands():
    advertised_ids = {command["id"] for command in load_async_http_catalog()}
    routes = set(re.findall(r'app\.add_route\("/v1/do/([^"]+)"', ASYNC_HTTP_MAIN_PATH.read_text()))

    assert routes == advertised_ids


def test_aggregate_execution_routes_match_advertised_commands():
    advertised_ids = {command["id"] for command in json.loads(AGGREGATE_COMMANDS_PATH.read_text())}
    routes = set(re.findall(r"location = /standard/v1/do/([^ ]+) \{", AGGREGATE_NGINX_PATH.read_text()))

    assert routes == advertised_ids


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
            "CommandInvocation",
            paths["/v1/do/{connector}/{command}"]["post"]["requestBody"]["content"]["application/json"]["example"],
        ),
        (
            "ConnectorProxyResponseV2",
            paths["/v1/do/{connector}/{command}"]["post"]["responses"]["200"]["content"]["application/json"]["example"],
        ),
        (
            "ConnectorProxyResponseV2",
            paths["/v1/do/{connector}/{command}"]["post"]["responses"]["202"]["content"]["application/json"]["example"],
        ),
        ("CommandCatalog", paths["/v1/auths"]["get"]["responses"]["200"]["content"]["application/json"]["example"]),
    ]
    callback = paths["/v1/do/{connector}/{command}"]["post"]["callbacks"]["commandCompleted"]
    callback_operation = callback["{$request.body#/spiff__callback_url}"]["put"]
    component_examples.append(
        (
            "ConnectorProxyResponseV2",
            callback_operation["requestBody"]["content"]["application/json"]["example"],
        )
    )
    component_responses = protocol["components"]["responses"]
    component_examples.extend(
        [
            (
                "ConnectorProxyProtocolError",
                component_responses["ProtocolError"]["content"]["application/json"]["example"],
            )
        ]
    )

    for schema_name, example in component_examples:
        protocol_validator(schema_name).validate(example)

    unauthorized_media = component_responses["Unauthorized"]["content"]["application/json"]
    Draft202012Validator(unauthorized_media["schema"]).validate(unauthorized_media["example"])

    liveness_media = paths["/v1/liveness"]["get"]["responses"]["200"]["content"]["application/json"]
    for example in liveness_media["examples"].values():
        Draft202012Validator(liveness_media["schema"]).validate(example["value"])
