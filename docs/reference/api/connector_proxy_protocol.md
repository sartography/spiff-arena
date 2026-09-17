# Connector proxy protocol

This page defines the HTTP contract between Spiff Arena and a connector proxy.
New proxy implementations should follow it. The
[OpenAPI 3.1 document](https://github.com/sartography/spiff-arena/blob/main/connector-proxies/protocol/openapi.json)
contains the same request and response schemas in machine-readable form.

## Protocol surface

A conforming connector proxy implements two required operations and may
implement authentication discovery:

| Operation | Purpose | Requirement |
| --- | --- | --- |
| `GET /v1/commands` | Advertise commands and their parameters | Required |
| `POST /v1/do/{connector}/{command}` | Execute one advertised command | Required |
| `GET /v1/auths` | Advertise connector-managed authentication handlers | Optional |

The base URL is set in
`SPIFFWORKFLOW_BACKEND_CONNECTOR_PROXY_URL`. Arena appends the paths above
without inserting another path segment.

The protocol version in the URL and `command_response_version` serve different
purposes. `/v1` versions the proxy HTTP interface.
`command_response_version: 2` selects the response envelope described below.

## Command discovery

`GET /v1/commands` must return `200 OK` and a JSON array. Each item has this
form:

```json
{
  "id": "example/Example",
  "parameters": [
    {
      "id": "message",
      "type": "str",
      "required": true
    }
  ]
}
```

`id` consists of a connector name and a command name separated by one slash.
Arena sends that value as the final two segments of the execution URL.
Connector and command names therefore must not contain `/`.

Each parameter description contains:

- `id`, the key accepted in the execution request;
- `type`, one of `str`, `int`, `bool`, or `any`; and
- `required`, a boolean.

The catalog describes the fields presented for configuration in Arena. It is
not a complete JSON Schema for a command. A proxy may add fields to command and
parameter descriptions. Arena ignores fields it does not understand.

Command ids should be unique. If an external proxy advertises an id also
provided by Arena's embedded connectors, Arena retains the embedded command.

## Command execution

Arena executes `example/Example` with:

```text
POST /v1/do/example/Example
Content-Type: application/json
User-Agent: spiffworkflow-backend
```

The JSON object contains the parameters configured on the BPMN service task.
Arena also adds these reserved fields:

| Field | Type | Meaning |
| --- | --- | --- |
| `spiff__process_instance_id` | integer or null | Arena process instance id |
| `spiff__process_model_identifier` | string or null | Process model identifier |
| `spiff__task_id` | string | Service task UUID |
| `spiff__task_data` | object | Current task data |
| `spiff__callback_url` | URI | Arena endpoint for asynchronous completion |

The `spiff__` prefix is reserved for Arena. A connector-specific parameter
must not use it.

A proxy should reject a missing required command parameter with a clear error.
It may ignore reserved metadata it does not use. The
`spiffworkflow-proxy` library removes unused `spiff__` fields before it
constructs a synchronous command object.

## Version 2 response envelope

New proxies must return JSON in this form for a dispatched command:

```json
{
  "command_response": {
    "body": {
      "connector_response": "done"
    },
    "mimetype": "application/json",
    "http_status": 200,
    "headers": {}
  },
  "command_response_version": 2,
  "error": null,
  "spiff__logs": []
}
```

The top-level fields are:

| Field | Requirement | Meaning |
| --- | --- | --- |
| `command_response` | Required | Command result |
| `command_response_version` | Required | Integer `2` |
| `error` | Required | Error object or `null` |
| `spiff__logs` | Required | Strings Arena writes to its connector log |

`command_response` contains:

| Field | Requirement | Meaning |
| --- | --- | --- |
| `body` | Required | Result assigned to the service task |
| `mimetype` | Required | Media type of `body` |
| `http_status` | Optional | Status reported by the command or upstream service |
| `headers` | Optional | Headers the command chooses to expose |

`body` may hold any JSON value. For a normal synchronous completion, Arena
serializes the whole `command_response` object as the service task result. For
an asynchronous callback, Arena assigns `command_response.body` to the
configured result variable. Arena adds `operator_identifier` to synchronous
version 2 command responses before returning them to the workflow.

`spiff__logs` is not a private channel. A proxy must not put credentials,
tokens, request authorization headers, or sensitive response data in it.

## Status and error handling

There are two status values:

1. The connector proxy's HTTP response status describes transport and dispatch.
2. `command_response.http_status` describes the command result, often the
   status returned by an upstream HTTP service.

For synchronous command completion, a proxy should return outer `200` and put
an upstream status in `command_response.http_status`. Arena treats an inner
status of 300 or greater as a service task error even when the outer status is
200.

`error`, when non-null, must contain string `error_code` and `message` fields:

```json
{
  "error": {
    "error_code": "TIMEOUT_ERROR",
    "message": "The upstream request timed out."
  }
}
```

Arena parses the response as JSON before it evaluates status fields. It handles
failures in this order:

1. A response that is not valid JSON is a proxy failure.
2. A structured `error` with `error_code` is a command failure.
3. Otherwise, `command_response.http_status >= 300` is a command failure.
4. Otherwise, an outer status of 300 or greater is a proxy failure.

An error boundary event on the service task may catch the resulting error
code. If no boundary event catches it, the process instance enters an error
state.

A proxy that cannot dispatch a command may return a non-2xx status with the
minimal error envelope retained by older implementations:

```json
{
  "command_response": {},
  "error": {
    "error_code": "command_not_found",
    "message": "The command does not exist."
  }
}
```

Once a command has been dispatched, the complete version 2 envelope is
preferred for both success and failure.

## Asynchronous completion

Arena leaves the service task waiting only when the outer response is
`202 Accepted`, the body is valid JSON, the envelope has no structured error,
and `command_response.http_status` is absent or below 300.
`command_response.http_status: 202` alone does not make the task wait.

An accepted response still uses the version 2 envelope. Its body may contain
job metadata, but Arena does not use that body to decide whether to wait.

After the work finishes, the worker sends a `PUT` request to the exact
`spiff__callback_url` supplied in the execution request. A successful callback
must contain `command_response.body`. An error callback must contain a
structured `error`. Other version 2 envelope fields may be included. See the
[callback examples](../../explanation/dev/connector_proxy_examples.md#using-callback-urls-long-running-tasks)
for complete request and response bodies.

The callback URL is an Arena API endpoint. Possession of the URL does not grant
access. The callback caller must authenticate and must be authorized to update
the process instance under the target Arena deployment's policy. An anonymous
caller, or a user without access to that process instance, receives `401` or
`403`. A malformed body, an unknown task, or a task that is no longer waiting
receives `400`.

Callbacks are not idempotent after completion. A worker should record the
outcome and stop retrying after Arena accepts the callback. Service task retry
configuration may cause Arena to schedule another attempt when a callback
reports a command error.

## Transport security

Arena sends `Spiff-Connector-Proxy-Api-Key` on discovery, authentication
discovery, and execution requests when
`SPIFFWORKFLOW_BACKEND_CONNECTOR_PROXY_API_KEY` is configured. A proxy that
uses this mechanism must compare the value against its configured secret and
return `401` when it is absent or wrong.

The header authenticates Arena to the proxy. It does not authenticate the
proxy or an asynchronous worker to Arena's callback endpoint.

Use HTTPS whenever requests cross a trusted network boundary. Treat command
parameters and task data as sensitive. A proxy should use bounded connection
and response timeouts, redact secrets from logs, and allow only required
cross-origin callers. CORS is not required for backend-to-proxy traffic.

## Optional extensions

### Authentication discovery

`GET /v1/auths` uses the command catalog shape to advertise connector-managed
authentication handlers. A proxy without such handlers may omit the endpoint
or return an empty array. Arena treats a non-200 response as an empty list.

The browser redirect routes implemented by `spiffworkflow-proxy` are not part
of this protocol. Their provider configuration, session storage, callback
parameters, and redirect allowlists are deployment-specific.

### Aggregation and redirects

A proxy may aggregate catalogs from several services. Execution may return an
HTTP 307 or 308 redirect to another proxy, provided the client can reach the
target and the redirect preserves the POST method, body, and authentication
policy. Do not use 301, 302, or 303 for command routing because clients may
change POST to GET. The redirect target receives the complete invocation,
including task data and resolved command parameters, and the connector-proxy
API-key header. Treat every redirect target as part of the same trusted
security boundary.

## Legacy compatibility

Arena still accepts older unversioned command responses. Some versions of
`spiffworkflow-proxy` also accept GET on execution routes, return a minimal
envelope for dispatch errors, and expose additional utility routes. These
behaviors exist for compatibility. New implementations should use POST and the
version 2 envelope.

Consumers must tolerate additional fields in discovery descriptions,
invocations, command responses, and errors. Arena reserves legacy response
fields with special behavior: `api_response` may replace the parsed result,
while `refreshed_token_set` triggers secret refresh and requires matching
`auth` and `api_response` fields. Producers must not reuse these names for
other purposes or change the meaning of a defined field without a new protocol
version.
