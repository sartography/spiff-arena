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


def test_setup_logger_obscures_preconfigured_sqlalchemy_handler_at_debug(monkeypatch: pytest.MonkeyPatch) -> None:
    app = Flask("preconfigured_sqlalchemy_logger_test")
    app.config.update(
        ENV_IDENTIFIER="non_local",
        SPIFFWORKFLOW_BACKEND_EVENT_STREAM_HOST=None,
        SPIFFWORKFLOW_BACKEND_LOG_LEVEL="debug",
        SPIFFWORKFLOW_BACKEND_LOG_TO_FILE=False,
        SPIFFWORKFLOW_BACKEND_LOGGERS_TO_USE="",
    )
    sqlalchemy_logger = logging.getLogger("sqlalchemy.engine.Engine")
    preconfigured_handler = logging.StreamHandler()
    monkeypatch.setattr(sqlalchemy_logger, "handlers", [preconfigured_handler])
    monkeypatch.setattr(logging.root.manager, "loggerDict", {sqlalchemy_logger.name: sqlalchemy_logger})

    setup_logger_for_app(app, logging)

    assert sqlalchemy_logger.level == logging.ERROR
    assert preconfigured_handler.level == logging.ERROR
