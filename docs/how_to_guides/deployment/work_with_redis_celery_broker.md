# Configure Celery Background Processing

SpiffWorkflow can use Celery to run background work outside the API request process.
Features such as asynchronous message execution, process metadata backfill, and task-available process hooks require Celery.

## Required Configuration

Enable Celery and configure a broker and result backend for every backend container that participates in process execution, including the API, background scheduler, and Celery worker:

```bash
SPIFFWORKFLOW_BACKEND_CELERY_ENABLED=true
SPIFFWORKFLOW_BACKEND_CELERY_BROKER_URL=...
SPIFFWORKFLOW_BACKEND_CELERY_RESULT_BACKEND=...
```

If you use SQS as the broker, also configure:

```bash
SPIFFWORKFLOW_BACKEND_CELERY_SQS_URL=...
```

If you use S3 as the result backend, also configure:

```bash
SPIFFWORKFLOW_BACKEND_CELERY_RESULT_S3_BUCKET=...
```

The Celery worker entrypoint is:

```bash
./bin/start_celery_worker
```

For more on splitting backend containers in a deployment, see [Deploy](/how_to_guides/deployment/deploy).

## Redis Broker and Result Backend

Redis can be used as both a broker and result backend for Celery.
For example:

```bash
SPIFFWORKFLOW_BACKEND_CELERY_BROKER_URL=redis://spiff-redis:6379
SPIFFWORKFLOW_BACKEND_CELERY_RESULT_BACKEND=redis://spiff-redis:6379
```

If configured in this way, there will be a queue called "celery," and you can inspect it from redis-cli like this:

```sh
redis-cli LLEN celery # how many queued entries
redis-cli LRANGE celery 0 -1 # get all queued entries. Be careful if you have a lot.
```

If you want to purge all entries from the queue:

```sh
poetry run celery -A src.spiffworkflow_backend.background_processing.celery_worker purge
```

If you want to inspect jobs that are currently being processed by workers:

```sh
poetry run celery -A src.spiffworkflow_backend.background_processing.celery_worker inspect active
```

When we publish a message to the queue, we log a message like this at the log level info:

```sh
Queueing process instance (3) for celery (9622ff55-9f23-4a94-b4a0-4e0a615a8d14)
```

If you want to get the results of this job after the worker processes it, you would run a query like this:

```sh
redis-cli get celery-task-meta-9622ff55-9f23-4a94-b4a0-4e0a615a8d14
```

As such, if you wanted to get ALL of the results, you could use a command like:

```sh
echo 'keys celery-task-meta-\*' | redis-cli | sed 's/^/get /' | redis-cli
```
