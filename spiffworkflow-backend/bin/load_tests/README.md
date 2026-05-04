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
instance.

To include the cold BPMN process-definition persistence path in the same stress test:

```sh
uv run python bin/load_tests/concurrent_message_starts.py --requests 50 --workers 20 --no-warm-up
```

Useful options:

```sh
uv run python bin/load_tests/concurrent_message_starts.py --help
```
