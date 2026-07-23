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

TTL is currently limited to a short window.
Use the generated OpenAPI documentation for the current maximum.
