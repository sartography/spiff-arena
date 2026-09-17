# Connector proxy protocol

This page defines the HTTP contract between Spiff Arena and a connector proxy.
It is the normative reference for new proxy implementations. The
[OpenAPI 3.1 document](https://github.com/sartography/spiff-arena/blob/main/connector-proxies/protocol/openapi.json)
contains the same request and response schemas in machine-readable form.

The words **MUST**, **MUST NOT**, **SHOULD**, and **MAY** state conformance
requirements.

## Protocol surface

A conforming connector proxy implements two operations:

| Operation | Purpose | Requirement |
| --- | --- | --- |
| `GET /v1/commands` | Advertise commands and their parameters | Required |
| `POST /v1/do/{connector}/{command}` | Execute one advertised command | Required |
| `GET /v1/auths` | Advertise connector-managed authentication handlers | Optional |
| `GET /v1/liveness` | Report process liveness | Optional |

The base URL is set in
`SPIFFWORKFLOW_BACKEND_CONNECTOR_PROXY_URL`. Arena appends the paths above
without inserting another path segment.

The protocol version in the URL and `command_response_version` serve different
purposes. `/v1` versions the proxy HTTP interface.
`command_response_version: 2` selects the response envelope described below.

## Command discovery

`GET /v1/commands` MUST return `200 OK` and a JSON array. Each item has this
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
Connector and command names therefore MUST NOT contain `/`.

Each parameter description contains:

- `id`, the key accepted in the execution request;
- `type`, one of `str`, `int`, `bool`, or `any`; and
- `required`, a boolean.

The catalog describes the fields presented for configuration in Arena. It is
not a complete JSON Schema for a command. A proxy MAY add fields to command and
parameter descriptions. Arena ignores fields it does not understand.

Command ids SHOULD be unique. If an external proxy advertises an id also
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
MUST NOT use it.

A proxy SHOULD reject a missing required command parameter with a clear error.
It MAY ignore reserved metadata it does not use. The
`spiffworkflow-proxy` library removes unused `spiff__` fields before it
constructs a synchronous command object.

## Version 2 response envelope

New proxies MUST return JSON in this form for a dispatched command:

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
configured result variable.

`spiff__logs` is not a private channel. A proxy MUST NOT put credentials,
tokens, request authorization headers, or sensitive response data in it.

## Status and error handling

There are two status values:

1. The connector proxy's HTTP response status describes transport and dispatch.
2. `command_response.http_status` describes the command result, often the
   status returned by an upstream HTTP service.

For synchronous command completion, a proxy SHOULD return outer `200` and put
an upstream status in `command_response.http_status`. Arena treats an inner
status of 300 or greater as a service task error even when the outer status is
200.

`error`, when non-null, MUST contain string `error_code` and `message` fields:

```json
{
  "error": {
    "error_code": "TIMEOUT_ERROR",
    "message": "The upstream request timed out."
  }
}
```

Arena handles failures in this order:

1. A structured `error` with `error_code` is a command failure.
2. Otherwise, `command_response.http_status >= 300` is a command failure.
3. Otherwise, an outer status of 300 or greater is a proxy failure.
4. A response that is not valid JSON is a proxy failure.

An error boundary event on the service task may catch the resulting error
code. If no boundary event catches it, the process instance enters an error
state.

A proxy that cannot dispatch a command MAY return a non-2xx status with the
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

Outer HTTP `202 Accepted` is the only signal that tells Arena to leave the
service task waiting. `command_response.http_status: 202` does not have that
effect.

An accepted response still uses the version 2 envelope:

```text
HTTP/1.1 202 Accepted
Content-Type: application/json

{
  "command_response": {
    "body": {
      "job_id": "job-123"
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

Arena checks the envelope for errors before it acts on the outer 202. A proxy
MUST NOT return 202 with a non-null error when it intends the task to wait.

After the work finishes, the worker sends a `PUT` request to the exact
`spiff__callback_url` supplied in the execution request. The callback body uses
the same version 2 envelope. `command_response.body` is required:

```json
{
  "command_response": {
    "body": {
      "job_id": "job-123",
      "status": "complete"
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

The callback URL is an Arena API endpoint. Possession of the URL does not grant
access. The callback caller MUST authenticate and MUST be authorized to update
the process instance under the target Arena deployment's policy. An anonymous
caller, or a user without access to that process instance, receives `401` or
`403`. A malformed body, an unknown task, or a task that is no longer waiting
receives `400`.

Callbacks are not idempotent after completion. A worker SHOULD record the
outcome and stop retrying after Arena accepts the callback. Service task retry
configuration may cause Arena to schedule another attempt when a callback
reports a command error.

## Transport security

Arena sends `Spiff-Connector-Proxy-Api-Key` on discovery, authentication
discovery, and execution requests when
`SPIFFWORKFLOW_BACKEND_CONNECTOR_PROXY_API_KEY` is configured. A proxy that
uses this mechanism MUST compare the value against its configured secret and
return `401` when it is absent or wrong.

The header authenticates Arena to the proxy. It does not authenticate the
proxy or an asynchronous worker to Arena's callback endpoint.

Use HTTPS whenever requests cross a trusted network boundary. Treat command
parameters and task data as sensitive. A proxy SHOULD use bounded connection
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

### Liveness

`GET /v1/liveness` may return any JSON object with outer status 200 when the
proxy process can receive requests. It does not prove that downstream services
are reachable. The older `/liveness` path is a compatibility alias, not a
required endpoint.

### Aggregation and redirects

A proxy may aggregate catalogs from several services. Execution may return an
HTTP 307 or 308 redirect to another proxy, provided the client can reach the
target and the redirect preserves the POST method, body, and authentication
policy. Do not use 301, 302, or 303 for command routing because clients may
change POST to GET.

## Legacy compatibility

Arena still accepts older unversioned command responses. Some versions of
`spiffworkflow-proxy` also accept GET on execution routes, return a minimal
envelope for dispatch errors, and expose `/liveness`. These behaviors exist for
compatibility. New implementations should use POST, the version 2 envelope,
and `/v1/liveness`.

Consumers must tolerate additional fields in discovery descriptions,
invocations, response envelopes, command responses, and errors. Producers must
not change the meaning of a defined field without a new protocol version.

## Implementation checklist

A new proxy is ready for Arena when:

- `GET /v1/commands` returns a catalog that matches the OpenAPI schema;
- every advertised id has a matching POST route;
- required command parameters are enforced;
- reserved `spiff__` fields are accepted without reaching constructors that
  do not declare them;
- every dispatched command returns a version 2 JSON envelope;
- structured errors have stable `error_code` values;
- only an outer 202 starts asynchronous waiting;
- callback workers can authenticate to Arena and always include
  `command_response.body`;
- API keys and sensitive command data are not logged;
- outbound calls have explicit timeouts; and
- contract tests cover discovery, success, command failure, dispatch failure,
  asynchronous acceptance, and callback completion.
