# Messages API

The messages API lets an external system send a BPMN message into SpiffWorkflow.
It can start a process through a Message Start Event or continue a running process that is waiting at a matching catch/receive message.

For the full request and response schema, use the generated OpenAPI documentation at `/v1.0/ui`.

## Send a Message

```bash
POST /v1.0/messages/{modified_message_name}
Content-Type: application/json

{"reference_id": 787862449}
```

`modified_message_name` is the BPMN message name, with slashes replaced by colons when a process group prefix is needed.
For example, if the process group prefix is `orders` and the BPMN message name is `payment_failed`, post to:

```bash
POST /v1.0/messages/orders:payment_failed
```

The JSON body is the message payload used for correlation.
Do not add a `payload` wrapper unless your message's retrieval expressions explicitly expect that field.

## JSON Schema Validation

The endpoint requires a JSON object, but currently does **not** validate it against the JSON schema
stored on the shared message model. A schema in the Message Editor does not make required fields,
field types, or `additionalProperties` restrictions enforceable at `/messages`.
Validate incoming data explicitly in your process or integration when those checks are required.

## Correlating With a Running Process

The message name identifies the kind of message. Correlation values identify the waiting process.
Configure the message's **Correlation Properties** in the Message Editor and, when the expected
value comes from task data, configure **Matching Conditions** on the receiving task or event.

For example:

| Setting | Value |
| --- | --- |
| Correlation property identifier | `order_id` |
| Message retrieval expression | `callback["orderId"]` |
| Receiving task's matching condition for `order_id` | `order["id"]` |

With task data `{"order": {"id": 123}}`, post `{"callback": {"orderId": 123}}`.
The retrieval expression runs against the posted JSON; the matching condition runs against task data
when the receiving task becomes active. Their results must compare equal; the string `"123"` does not
match the integer `123`.
The property identifier connects these two settings; it does not automatically look up a task variable.

Expressions use Python dictionary access for nested JSON, such as `callback["orderId"]`.
JavaScript-style dot notation such as `callback.orderId` does not access a plain JSON dictionary.

A matching condition is not required when the workflow already has the expected correlation value
from an earlier message. If you need to establish that value from task data, enable condition matching
and supply the expression. Merely defining a correlation property does not establish an expected value:
a receiver with no saved correlation values can accept a message by name alone.
See [Send and Receive Messages Between Processes](/how_to_guides/building_diagrams/send_and_receive_messages)
for the editor configuration.

## Matching Behavior

If the message matches a waiting process instance, SpiffWorkflow correlates the message and returns `200`.

If the message matches a Message Start Event, SpiffWorkflow starts or reserves the process and returns `200`.

If there is no match and no buffering is requested, the request returns `400` with `message_not_accepted`.

The messages list in the UI can help debug whether a message was accepted, buffered, completed, or rejected.

## Execution Mode

Set `execution_mode=asynchronous` to use Celery when it is enabled:

```bash
POST /v1.0/messages/orders:payment_failed?execution_mode=asynchronous
```

Asynchronous execution requires Celery background processing.
For setup details, see [Configure Celery Background Processing](/how_to_guides/deployment/work_with_redis_celery_broker).

For a Message Start Event, SpiffWorkflow reserves a process instance, queues its BPMN initialization and message delivery,
and returns `200`. The response includes the reserved process instance with its real `id` and an initial status of
`not_started`, so callers can refer to it immediately. The process may still be `not_started` when it is first retrieved;
the Celery worker updates that same process instance as execution proceeds.

For a message that matches an existing waiting process instance, message delivery is completed before the response and
continued process execution is queued as before.

## Buffering Unmatched Messages

External systems often cannot guarantee that a callback arrives after the process is already waiting for it.
Use `time_to_live_in_seconds` to buffer an unmatched message briefly:

```bash
POST /v1.0/messages/billing:payment_callback?time_to_live_in_seconds=60&message_instance_uuid=2d15e8cc-98dd-448c-bff6-66dbce9f5f2c
Content-Type: application/json

{"event_uuid": "1ac1370c-4bf3-4012-be44-6e5bf7caaf07"}
```

When `time_to_live_in_seconds` is greater than `0`, `message_instance_uuid` is required.
The UUID is an idempotency key: retrying the same message with the same UUID returns the existing message instead of creating a duplicate.

If the TTL elapses before any process instance correlates with the message, SpiffWorkflow marks the
message instance `expired` instead of leaving it buffered. The message instance keeps a `failure_cause`
that says whether any process instance was waiting and lists the correlation values found in the payload.
A retry with the same `message_instance_uuid` returns that expired message instance rather than creating a
new buffered message.

TTL is currently limited to a short window.
Use the generated OpenAPI documentation for the current maximum.
