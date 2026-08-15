from flask import Flask

from spiffworkflow_backend.background_processing.celery import celery_init_app


def test_celery_enables_task_events_for_flower() -> None:
    app = Flask("spiffworkflow_backend")
    app.config["SPIFFWORKFLOW_BACKEND_CELERY_BROKER_URL"] = "redis://localhost:6379/0"

    celery_app = celery_init_app(app)

    assert celery_app.conf.worker_send_task_events is True
    assert celery_app.conf.task_send_sent_event is True
