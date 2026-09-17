# Connector proxy protocol

[`openapi.json`](openapi.json) is the machine-readable definition of the HTTP
contract between Spiff Arena and a connector proxy. The corresponding prose is
in the
[connector proxy protocol reference](../../docs/reference/api/connector_proxy_protocol.md).

From the repository root, validate the schema with `uvx openapi-spec-validator connector-proxies/protocol/openapi.json`.

When the protocol changes, update the OpenAPI document and reference page
together, then run this command.
