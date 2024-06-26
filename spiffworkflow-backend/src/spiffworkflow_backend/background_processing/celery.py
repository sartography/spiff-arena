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
        "broker_url": app.config["SPIFFWORKFLOW_BACKEND_CELERY_BROKER_URL"],
        "result_backend": app.config["SPIFFWORKFLOW_BACKEND_CELERY_RESULT_BACKEND"],
        "task_ignore_result": True,
        "task_serializer": "json",
        "result_serializer": "json",
        "accept_content": ["json"],
        "enable_utc": True,
        "worker_redirect_stdouts_level": "DEBUG",
    }

    celery_app = Celery(app.name)
    celery_app.Task = FlaskTask  # type: ignore
    celery_app.config_from_object(celery_configs)
    celery_app.conf.update(app.config)
    celery_app.set_default()
    app.celery_app = celery_app
    return celery_app
