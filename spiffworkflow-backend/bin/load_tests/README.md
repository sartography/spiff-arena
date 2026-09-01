# Backend Load Tests

Start Spiff first, then run load tests from `spiffworkflow-backend`.

## Concurrent Message Starts

Use this for message-start concurrency regression testing:

```sh
uv run python bin/load_tests/concurrent_message_starts.py --requests 50 --workers 20
```

The script creates a temporary message-start process model using the API, then fires the requested number of concurrent
`POST /v1.0/messages/...` requests. This includes the cold BPMN process-definition persistence path. It exits nonzero if
any request fails or does not complete its own process instance, or if successful requests do not each return a distinct
process instance. HTTP latency is measured separately from the follow-up polling used to verify eventual process
completion.

To reproduce the 25-request asynchronous message-start latency case:

```sh
uv run python bin/load_tests/concurrent_message_starts.py \
  --requests 25 \
  --workers 25 \
  --execution-mode asynchronous \
  --max-http-latency-seconds 2
```

The summary reports HTTP min/p50/p95/max latency, concurrent-batch wall time, throughput, and the ten slowest requests.
When `--max-http-latency-seconds` is provided, the script exits nonzero if any request in the concurrent batch exceeds the
threshold. Completion polling is not included in this latency check.

Useful options:

```sh
uv run python bin/load_tests/concurrent_message_starts.py --help
```

To exercise a message start that is already deployed without creating a
temporary process model:

```sh
uv run python bin/load_tests/concurrent_message_starts.py \
  --skip-model-setup \
  --group-id existing-group \
  --message-name existing-message
```

## Concurrent Message Correlation Race

Use this for the vacuous message-correlation match, where a send whose correlation values belong to no waiting process
instance is still accepted by the API matcher and delivered to an arbitrary (oldest) ready receiver. The engine then
rejects the mismatched delivery and the innocent receiving process instance errors. The script creates a temporary
process model with two correlation keys per instance - one that the assessment message correlates on and one it has no
property for (like a scope key from a boundary message event) - starts the requested number of instances, sends a
message whose correlation matches no instance (correct code must reject it without erroring anything), then fires one
correctly-correlated send per instance concurrently.

```sh
uv run python bin/load_tests/concurrent_message_correlation_race.py
```

Defaults to 4 instances with short 15s waits, so failures surface quickly; scale up with `--instances` if you want more
load. Message requests are sent with `execution_mode=synchronous`, so the test does not depend on a Celery worker
draining queued message starts (without that parameter, a backend with `SPIFFWORKFLOW_BACKEND_CELERY_ENABLED=true`
queues message processing and the instances stay `not_started` until a worker picks them up).

The script exits nonzero if any process instance errors, if any send is delivered to a process instance other than the
one whose scope holds its correlation values, or if any instance fails to complete. Starts are sent sequentially (the
race under test is in concurrent delivery of correlated messages, not in message starts), and correctly-correlated
sends that land on `message_not_accepted` are retried briefly to avoid failing on background-scheduler lock contention.

Useful options:

```sh
uv run python bin/load_tests/concurrent_message_correlation_race.py --help
```

## Message Start Double Delivery Race

Use this for message-start races between API requests and background message processing. It covers the shape where a
message-start request returns 200, then the process instance later errors with
`WorkflowException: This process is not waiting for <message_name>`, and it can also surface rejected POSTs when a
background worker claims an API-created send message before the API handler finishes correlating it.

```sh
uv run python bin/load_tests/message_start_double_delivery_race.py --requests 200 --workers 40
```

The script creates a temporary message-start process model that parks each process instance on a manual task, sends many
identical `reference_id` message-start POSTs using asynchronous execution, waits for the background message processor window,
then re-fetches the returned process instances. Old vulnerable code can show process instances that were accepted and later
became `error`; fixed code should leave them in a non-error status.

For a heavier pre-fix repro attempt that spans multiple APScheduler ticks:

```sh
uv run python bin/load_tests/message_start_double_delivery_race.py --requests 200 --workers 40 --batches 6 --batch-delay-seconds 2 --settle-seconds 15
```

Useful options:

```sh
uv run python bin/load_tests/message_start_double_delivery_race.py --help
```

## BPMN Process Definition Relationship Race

Use this against an already-running backend for the cold process-definition persistence race where concurrent requests can
try to create the same `bpmn_process_definition_relationship` row. The script creates a temporary process model with a
call activity, then fires concurrent process-instance creates. It defaults to the Arena backend on port `7000`.

```sh
uv run python bin/load_tests/process_definition_relationship_race.py
```

Useful options:

```sh
uv run python bin/load_tests/process_definition_relationship_race.py --help
```

## Task Submission

Use this k6-based harness for parallel manual-task submission against a running backend. It creates its temporary process
model before running k6:

```sh
SPIFF_API_KEY="..." NUM_TASKS=10 ./bin/load_tests/task_submission/run_parallel_tasks_test.sh
```

See `bin/load_tests/task_submission/README.md` for setup details.
