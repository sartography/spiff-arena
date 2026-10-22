import logging
import os
import select
import socket
import subprocess
import sys
from pathlib import Path

import pytest
from flask import Flask

from spiffworkflow_backend.services.logging_service import JsonFormatter
from spiffworkflow_backend.services.logging_service import event_stream_peer_has_closed
from spiffworkflow_backend.services.logging_service import setup_logger_for_app
from spiffworkflow_backend.services.logging_service import skip_successful_probe_access_record


def test_import_creates_missing_prometheus_multiproc_dir(tmp_path: Path) -> None:
    multiproc_dir = tmp_path / "prometheus_multiproc"
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", "import spiffworkflow_backend.services.logging_service"],
        env={**os.environ, "PROMETHEUS_MULTIPROC_DIR": str(multiproc_dir)},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert multiproc_dir.is_dir()


@pytest.mark.parametrize("use_poll", [True, False])
def test_event_stream_peer_has_closed(monkeypatch: pytest.MonkeyPatch, use_poll: bool) -> None:
    if use_poll:
        if not hasattr(select, "poll"):
            pytest.skip("poll is unavailable")

        def unexpected_select(*args: object) -> None:
            pytest.fail("poll should be preferred over select")

        monkeypatch.setattr(select, "select", unexpected_select)
    else:
        monkeypatch.delattr(select, "poll", raising=False)

    sock, peer = socket.socketpair()
    with sock, peer:
        sock.settimeout(0.5)
        assert not event_stream_peer_has_closed(sock)
        peer.sendall(b"a")
        assert not event_stream_peer_has_closed(sock)
        assert sock.recv(1) == b"a"  # The readiness check must not consume data.
        peer.close()
        assert event_stream_peer_has_closed(sock)
    assert event_stream_peer_has_closed(sock)


def test_event_stream_peer_has_closed_with_high_descriptor() -> None:
    if not hasattr(select, "poll"):
        pytest.skip("poll is unavailable")
    fcntl = pytest.importorskip("fcntl")
    resource = pytest.importorskip("resource")
    soft_limit, _ = resource.getrlimit(resource.RLIMIT_NOFILE)
    if soft_limit != resource.RLIM_INFINITY and soft_limit <= 1024:
        pytest.skip("RLIMIT_NOFILE does not permit descriptor 1024")
    sock, peer = socket.socketpair()
    with sock, peer:
        with socket.socket(fileno=fcntl.fcntl(sock, fcntl.F_DUPFD, 1024)) as high_sock:
            high_sock.settimeout(0.5)
            assert not event_stream_peer_has_closed(high_sock)
            peer.close()
            assert event_stream_peer_has_closed(high_sock)


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
    previous_logger_level = sqlalchemy_logger.level
    previous_logger_propagate = sqlalchemy_logger.propagate
    previous_handler_level = preconfigured_handler.level
    previous_handler_formatter = preconfigured_handler.formatter

    try:
        setup_logger_for_app(app, logging)

        assert sqlalchemy_logger.level == logging.ERROR
        assert preconfigured_handler.level == logging.ERROR
    finally:
        sqlalchemy_logger.setLevel(previous_logger_level)
        sqlalchemy_logger.propagate = previous_logger_propagate
        preconfigured_handler.setLevel(previous_handler_level)
        preconfigured_handler.setFormatter(previous_handler_formatter)


@pytest.mark.parametrize("has_preconfigured_handler", [True, False])
def test_setup_logger_keeps_kombu_at_info_at_debug(monkeypatch: pytest.MonkeyPatch, has_preconfigured_handler: bool) -> None:
    app = Flask("kombu_logger_test")
    app.config.update(
        ENV_IDENTIFIER="non_local",
        SPIFFWORKFLOW_BACKEND_EVENT_STREAM_HOST=None,
        SPIFFWORKFLOW_BACKEND_LOG_LEVEL="debug",
        SPIFFWORKFLOW_BACKEND_LOG_TO_FILE=False,
        SPIFFWORKFLOW_BACKEND_LOGGERS_TO_USE="",
    )
    kombu_logger = logging.getLogger("kombu.pidbox")
    monkeypatch.setattr(kombu_logger, "handlers", [logging.StreamHandler()] if has_preconfigured_handler else [])
    monkeypatch.setattr(kombu_logger, "level", kombu_logger.level)
    monkeypatch.setattr(kombu_logger, "propagate", kombu_logger.propagate)
    monkeypatch.setattr(logging.root.manager, "loggerDict", {kombu_logger.name: kombu_logger})

    setup_logger_for_app(app, logging)

    assert kombu_logger.level == logging.INFO
    assert [handler.level for handler in kombu_logger.handlers] == [logging.INFO]


def _uvicorn_access_record(method: str, path: str, status_code: int) -> logging.LogRecord:
    access_args = ("127.0.0.1:5000", method, path, "1.1", status_code)
    return logging.LogRecord("uvicorn.access", logging.INFO, __file__, 0, '%s - "%s %s HTTP/%s" %d', access_args, None)


@pytest.mark.parametrize(
    ("method", "path", "status_code", "logged"),
    [
        ("GET", "/api/v1.0/status", 200, False),
        ("GET", "/metrics", 200, False),
        ("GET", "/metrics?name[]=x", 200, False),
        ("GET", "/api/v1.0/status", 503, True),
        ("POST", "/api/v1.0/status", 200, True),
        ("GET", "/api/v1.0/tasks", 200, True),
    ],
)
def test_skip_successful_probe_access_record(method: str, path: str, status_code: int, logged: bool) -> None:
    assert skip_successful_probe_access_record(_uvicorn_access_record(method, path, status_code)) is logged


def test_skip_successful_probe_access_record_keeps_records_without_access_args() -> None:
    record = logging.LogRecord("uvicorn.access", logging.INFO, __file__, 0, "plain message", None, None)
    assert skip_successful_probe_access_record(record) is True
