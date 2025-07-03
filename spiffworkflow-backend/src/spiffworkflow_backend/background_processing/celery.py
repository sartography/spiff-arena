import flask.wrappers
from celery import Celery
from celery import Task


def init_celery_if_appropriate(app: flask.app.Flask) -> None:
    if app.config["SPIFFWORKFLOW_BACKEND_CELERY_ENABLED"]:
        celery_app = celery_init_app(app)
        app.celery_app = celery_app


def celery_init_app(app: flask.app.Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)  # type: ignore

    celery_configs = {
        "task_ignore_result": True,
        "task_serializer": "json",
        "result_serializer": "json",
        "accept_content": ["json"],
        "enable_utc": True,
        "worker_redirect_stdouts_level": "DEBUG",
    }

    broker_url = app.config["SPIFFWORKFLOW_BACKEND_CELERY_BROKER_URL"]

    # Configure SQS broker
    if broker_url.lower().startswith("sqs://"):
        sqs_url = app.config.get("SPIFFWORKFLOW_BACKEND_CELERY_SQS_URL")
        if sqs_url:
            celery_configs["broker_transport_options"] = {"predefined_queues": {"celery": {"url": sqs_url}}}
        else:
            raise ValueError("CELERY_BROKER_URL is set to sqs:// but SPIFFWORKFLOW_BACKEND_CELERY_SQS_URL is not set.")

    celery_configs["broker_url"] = broker_url

    result_backend = app.config.get("SPIFFWORKFLOW_BACKEND_CELERY_RESULT_BACKEND")
    if result_backend:
        if result_backend.startswith("s3://"):
            s3_bucket = app.config.get("SPIFFWORKFLOW_BACKEND_CELERY_RESULT_S3_BUCKET")
            if s3_bucket:
                celery_configs["s3_bucket"] = app.config.get("SPIFFWORKFLOW_BACKEND_CELERY_RESULT_S3_BUCKET")
            else:
                raise ValueError(
                    "CELERY_RESULT_BACKEND is set to s3:// but SPIFFWORKFLOW_BACKEND_CELERY_RESULT_S3_BUCKET is not set."
                )

        celery_configs["result_backend"] = result_backend

    celery_app = Celery(app.name)
    celery_app.Task = FlaskTask  # type: ignore
    celery_app.config_from_object(celery_configs)
    celery_app.conf.update(app.config)
    celery_app.set_default()
    app.celery_app = celery_app
    return celery_app
