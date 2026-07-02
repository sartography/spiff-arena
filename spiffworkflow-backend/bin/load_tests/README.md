# Backend Load Tests

Start Spiff first, then run load tests from `spiffworkflow-backend`.

## Concurrent Message Starts

Use this for message-start concurrency regression testing:

```sh
uv run python bin/load_tests/concurrent_message_starts.py --requests 50 --workers 20
```

The script creates a temporary message-start process model using the API, sends one warm-up message, then fires concurrent
`POST /v1.0/messages/...` requests. The warm-up keeps this focused on message-start concurrency rather than the separate
cold BPMN process-definition persistence path. It exits nonzero if any request fails or does not complete its own process
instance, or if successful requests do not each return a distinct process instance.

To include the cold BPMN process-definition persistence path in the same stress test:

```sh
uv run python bin/load_tests/concurrent_message_starts.py --requests 50 --workers 20 --no-warm-up
```

Useful options:

```sh
uv run python bin/load_tests/concurrent_message_starts.py --help
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
