# Redis Celery Broker

SpiffWorkflow can be configured to use Celery for efficient processing.
Redis can be used as both a broker and backend for Celery.

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
