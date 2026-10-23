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

The endpoint requires a JSON object. Schema validation is **off by default**. Set
`SPIFFWORKFLOW_BACKEND_VALIDATE_MESSAGE_BODY_AGAINST_SCHEMA=true` to validate external message bodies
once a recipient is selected. This does not change internally generated BPMN messages.

For a waiting process, lookup starts at the selected instance's process-model location. For a
Message Start Event, it starts at the selected triggerable process model. Upsearch takes the
nearest shared definition with that message name; definitions in other groups are not combined.
The caller's optional group prefix does not choose the schema or restrict message delivery.

Validation runs before consuming a waiting receiver or starting/reserving a process. Required fields,
field types, formats, and `additionalProperties` restrictions are enforced. A missing definition,
unset/empty schema, `{}`, or boolean `true` imposes no restrictions. Boolean `false` rejects every
payload. Invalid payloads and malformed schemas return `400` with `error_code: message_data_validation_error`.
The send record is retained as `not_accepted` with a diagnostic `failure_cause`; the receiver is left
waiting and its process is not failed. A corrected submission must use a new UUID if one was supplied.

**Buffering defers validation until a recipient is selected.** A `202` response means queued, not
schema-validated. At delivery time, the current schema applies. An invalid buffered message becomes
`not_accepted` with a `failure_cause`, visible in the messages list, without failing the waiting process.
Retrying that rejected message's UUID returns `400` with `message_not_accepted` and the diagnostic.

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
message instance `expired` during subsequent message handling, rather than delivering it. Cleanup is
opportunistic, not a timer guaranteed to run at the TTL deadline. A retry with the same
`message_instance_uuid` returns that expired message instance rather than creating a new buffered message.

The message instance keeps a `failure_cause` describing waiting receive events **at cleanup time**,
not necessarily at the TTL deadline. When receivers exist, it includes sampled correlation values
(up to 10 receivers and 20 distinct retrieval expressions). Values and the overall diagnostic are
truncated; an expression evaluation failure does not necessarily mean a field is missing.
This snapshot does not prove a correlation mismatch: a matching receiver may have been locked or
otherwise unable to accept delivery. Payload-derived values remain on the message record and are not
included in the structured expiry log.

The `spiff_message_send_expired_total` metric increments after the expiry transaction commits, with
reason `no_waiting_receiver` or `waiting_receiver_not_delivered`. As with other in-process counters,
it is best-effort telemetry, not an exactly-once audit record.

TTL is currently limited to a short window.
Use the generated OpenAPI documentation for the current maximum.
