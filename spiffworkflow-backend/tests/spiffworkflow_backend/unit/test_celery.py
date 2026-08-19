from typing import Any

from celery import _state
from flask import Flask

from spiffworkflow_backend.background_processing.celery import celery_init_app


def test_celery_enables_task_events_for_flower() -> None:
    app = Flask("spiffworkflow_backend")
    app.config["SPIFFWORKFLOW_BACKEND_CELERY_BROKER_URL"] = "redis://localhost:6379/0"
    celery_state: Any = _state
    previous_default_app = celery_state.default_app
    current_app_was_set = hasattr(celery_state._tls, "current_app")
    previous_current_app = getattr(celery_state._tls, "current_app", None)
    celery_app = None

    try:
        celery_app = celery_init_app(app)

        assert celery_app.conf.worker_send_task_events is True
        assert celery_app.conf.task_send_sent_event is True
    finally:
        celery_state.set_default_app(previous_default_app)
        if current_app_was_set:
            celery_state._tls.current_app = previous_current_app
        elif hasattr(celery_state._tls, "current_app"):
            del celery_state._tls.current_app
        if celery_app is not None:
            celery_app.close()
