# How to use

1. Start Spiff API.
1. Run `NUM_TASKS=10 ./bin/load_tests/task_submission/run_parallel_tasks_test.sh`

The script creates a temporary process group and process model, uploads `parallel-task.bpmn`, starts the process through
its message start event, and submits the generated manual tasks concurrently with k6.

Useful environment variables:

- `AUTH_METHOD`: `token` or `api_key`. Defaults to `token`, matching the Python load-test harnesses.
- `USERNAME`, `PASSWORD`, `CLIENT_ID`, `CLIENT_SECRET`, `OPENID_TOKEN_URL`, `AUTHENTICATION_IDENTIFIER`: token auth settings.
- `SPIFF_API_KEY`: service-account API key, required only when `AUTH_METHOD=api_key`.
- `BACKEND_BASE_URL`: backend URL used by the shell setup step. Defaults to `http://localhost:7000`.
- `API_HOST`: backend host used from inside the k6 Docker container. Defaults to `host.docker.internal:7000`.
- `PROCESS_GROUP_ID`: process group to create. Defaults to a unique `load_test/task_submission_*` group.
- `PROCESS_MODEL_ID`: process model to create. Defaults to `${PROCESS_GROUP_ID}/parallel-task`.
- `DB_CHECKS`: `auto`, `always`, or `never`. Defaults to `auto`, which runs direct MySQL diagnostics only when the
  process instance exists in the configured MySQL database.
- `MYSQL_DATABASE`: MySQL database for optional diagnostics. Defaults to `spiffworkflow_backend_local_development`.
- `MYSQL_USER`: MySQL user for optional diagnostics. Defaults to `root`.
- `MYSQL_HOST`: optional MySQL host for diagnostics.
- `SKIP_DB_CHECKS`: legacy alias; set to `true` to skip direct MySQL diagnostics after k6 runs.

To use service-account API-key auth:

```sh
AUTH_METHOD=api_key SPIFF_API_KEY="..." NUM_TASKS=10 ./bin/load_tests/task_submission/run_parallel_tasks_test.sh
```
