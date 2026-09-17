# Connector proxy protocol

[`openapi.json`](openapi.json) is the machine-readable definition of the HTTP
contract between Spiff Arena and a connector proxy. The corresponding prose is
in the
[connector proxy protocol reference](../../docs/reference/api/connector_proxy_protocol.md).

The backend contract test validates the schemas and checks them against the
embedded HTTP connector, the async HTTP proxy, and the aggregate proxy command
catalog:

```sh
cd spiffworkflow-backend
uv run pytest tests/spiffworkflow_backend/unit/test_connector_proxy_protocol.py
```

When the protocol changes, update the OpenAPI document, the reference page,
and the contract test in the same change.
