import logging

import pytest
from flask import Flask

from spiffworkflow_backend.services.logging_service import JsonFormatter
from spiffworkflow_backend.services.logging_service import setup_logger_for_app


def test_setup_logger_keeps_configured_level_for_handlerless_app_logger(monkeypatch: pytest.MonkeyPatch) -> None:
    app = Flask("handlerless_logger_test")
    app.logger.handlers = []
    app.logger.propagate = True
    app.config.update(
        ENV_IDENTIFIER="non_local",
        SPIFFWORKFLOW_BACKEND_EVENT_STREAM_HOST=None,
        SPIFFWORKFLOW_BACKEND_LOG_LEVEL="info",
        SPIFFWORKFLOW_BACKEND_LOG_TO_FILE=False,
        SPIFFWORKFLOW_BACKEND_LOGGERS_TO_USE="",
    )
    monkeypatch.setattr(logging.root.manager, "loggerDict", {app.logger.name: app.logger})

    setup_logger_for_app(app, logging)

    assert app.logger.level == logging.INFO
    assert len(app.logger.handlers) == 1
    assert app.logger.handlers[0].level == logging.INFO
    assert isinstance(app.logger.handlers[0].formatter, JsonFormatter)
