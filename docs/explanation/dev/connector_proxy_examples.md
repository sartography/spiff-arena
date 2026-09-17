# Connector Proxy API Examples

This page provides sample requests and responses for connector proxy implementations.

```{contents}
:local:
:depth: 2
```

## Request Examples

### List Available Commands

```bash
curl -s http://localhost:8200/v1/commands | jq
```

### Execute a GET Request

**Endpoint:**
```
POST /v1/do/http/GetRequest
```

**Request Payload:**
```json
{
  "url": "https://api.example.com/items",
  "headers": { "Accept": "application/json" },
  "params": { "limit": 10 }
}
```

### Execute a POST Request

**Endpoint:**
```
POST /v1/do/http/PostRequest
```

**Request Payload:**
```json
{
  "url": "https://api.example.com/items",
  "headers": { "Content-Type": "application/json" },
  "data": { "name": "example" }
}
```

`data` is sent as JSON by default. To send a form-encoded request body, set `body_format` to `form`:

```json
{
  "url": "https://auth.example.com/realms/demo/protocol/openid-connect/token",
  "headers": { "Content-Type": "application/x-www-form-urlencoded" },
  "body_format": "form",
  "data": {
    "grant_type": "password",
    "client_id": "admin-cli",
    "username": "admin",
    "password": "secret"
  }
}
```

### Execute a DELETE Request

**Endpoint:**
```
POST /v1/do/http/DeleteRequest
```

**Request Payload:**
```json
{
  "url": "https://api.example.com/items/123",
  "headers": { "Authorization": "Bearer token" }
}
```

### Execute a PUT Request

**Endpoint:**
```
POST /v1/do/http/PutRequest
```

**Request Payload:**
```json
{
  "url": "https://api.example.com/items/123",
  "headers": { "Content-Type": "application/json" },
  "data": { "name": "updated-example", "status": "active" }
}
```

### Execute a PATCH Request

**Endpoint:**
```
POST /v1/do/http/PatchRequest
```

**Request Payload:**
```json
{
  "url": "https://api.example.com/items/123",
  "headers": { "Content-Type": "application/json" },
  "data": { "status": "active" }
}
```

### Execute a HEAD Request

**Endpoint:**
```
POST /v1/do/http/HeadRequest
```

**Request Payload:**
```json
{
  "url": "https://api.example.com/items/123",
  "headers": { "Accept": "application/json" }
}
```

### Execute with Basic Authentication

```json
{
  "url": "https://api.example.com/secure",
  "basic_auth_username": "user",
  "basic_auth_password": "pass"
}
```

---

## Response Examples

Responses use the protocol's
[version 2 envelope](../../reference/api/connector_proxy_protocol.md#version-2-response-envelope).
The examples below show behavior specific to the async-http implementation.

### Non-JSON Response (Raw Text)

When the upstream service returns non-JSON content:

```json
{
  "command_response": {
    "body": {
      "raw_response": "Plain text response from the service"
    },
    "mimetype": "application/json",
    "http_status": 200
  },
  "command_response_version": 2,
  "error": null,
  "spiff__logs": []
}
```

### Error Response

When an error occurs:

```json
{
  "command_response": {
    "body": {},
    "mimetype": "application/json",
    "http_status": 500
  },
  "command_response_version": 2,
  "error": {
    "message": "Connection timeout",
    "error_code": "TIMEOUT_ERROR"
  },
  "spiff__logs": [
    "Attempted connection to https://api.example.com/items",
    "Request timed out after 30 seconds"
  ]
}
```

## Response Parsing Behavior

- If the upstream response `Content-Type` includes `application/json`, the proxy parses JSON into `command_response.body`
- Otherwise, the raw text is wrapped in:
  ```json
  { "raw_response": "<text>" }
  ```
- The `mimetype` field in the async-http example is set to `"application/json"` for all responses, including raw text responses

---

## Using Callback URLs (Long-Running Tasks)

When SpiffWorkflow invokes a service task, it automatically includes a `spiff__callback_url` parameter. If your service needs to process the request asynchronously:

1. Return an accepted response that satisfies the protocol's
   [asynchronous completion](../../reference/api/connector_proxy_protocol.md#asynchronous-completion)
   rules.
2. Call the callback URL later with credentials authorized to update the Arena
   process instance.

### Callback Request Format

When your service is ready to complete the task successfully, send a **PUT**
request to the `spiff__callback_url` with a `command_response.body`:

```text
PUT <spiff__callback_url>
Content-Type: application/json

{
  "command_response": {
    "body": {
      "order_id": "12345",
      "status": "complete",
      "details": "Processing finished successfully"
    },
    "mimetype": "application/json",
    "http_status": 200
  },
  "command_response_version": 2,
  "error": null,
  "spiff__logs": []
}
```

SpiffWorkflow stores `command_response.body` in the service task's configured
result variable. For error callbacks, authorization, and retry behavior, see
the protocol's [asynchronous completion](../../reference/api/connector_proxy_protocol.md#asynchronous-completion)
section. See
[Long-Running Service Tasks](../../how_to_guides/building_diagrams/long_running_service_tasks)
for process-model configuration.
