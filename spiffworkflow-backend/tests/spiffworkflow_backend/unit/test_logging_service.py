import io
import json
import logging
import os
import select
import socket
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from flask import Flask
from flask import g

from spiffworkflow_backend.services.logging_service import JsonFormatter
from spiffworkflow_backend.services.logging_service import LoggingService
from spiffworkflow_backend.services.logging_service import SpiffLogHandler
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


@pytest.mark.parametrize("logger_name", ["kombu.pidbox", "urllib3.connectionpool"])
@pytest.mark.parametrize("has_preconfigured_handler", [True, False])
def test_setup_logger_keeps_chatty_library_at_info_at_debug(
    monkeypatch: pytest.MonkeyPatch, logger_name: str, has_preconfigured_handler: bool
) -> None:
    app = Flask("chatty_library_logger_test")
    app.config.update(
        ENV_IDENTIFIER="non_local",
        SPIFFWORKFLOW_BACKEND_EVENT_STREAM_HOST=None,
        SPIFFWORKFLOW_BACKEND_LOG_LEVEL="debug",
        SPIFFWORKFLOW_BACKEND_LOG_TO_FILE=False,
        SPIFFWORKFLOW_BACKEND_LOGGERS_TO_USE="",
    )
    library_logger = logging.getLogger(logger_name)
    monkeypatch.setattr(library_logger, "handlers", [logging.StreamHandler()] if has_preconfigured_handler else [])
    monkeypatch.setattr(library_logger, "level", library_logger.level)
    monkeypatch.setattr(library_logger, "propagate", library_logger.propagate)
    monkeypatch.setattr(logging.root.manager, "loggerDict", {library_logger.name: library_logger})

    setup_logger_for_app(app, logging)

    assert library_logger.level == logging.INFO
    assert [handler.level for handler in library_logger.handlers] == [logging.INFO]


def test_setup_logger_logs_only_failed_flower_requests(monkeypatch: pytest.MonkeyPatch) -> None:
    app = Flask("flower_access_logger_test")
    app.config.update(
        ENV_IDENTIFIER="non_local",
        SPIFFWORKFLOW_BACKEND_EVENT_STREAM_HOST=None,
        SPIFFWORKFLOW_BACKEND_LOG_LEVEL="debug",
        SPIFFWORKFLOW_BACKEND_LOG_TO_FILE=False,
        SPIFFWORKFLOW_BACKEND_LOGGERS_TO_USE="",
    )
    tornado_access_logger = logging.getLogger("tornado.access")
    monkeypatch.setattr(tornado_access_logger, "handlers", [])
    monkeypatch.setattr(tornado_access_logger, "level", tornado_access_logger.level)
    monkeypatch.setattr(tornado_access_logger, "propagate", tornado_access_logger.propagate)
    monkeypatch.setattr(logging.root.manager, "loggerDict", {tornado_access_logger.name: tornado_access_logger})

    setup_logger_for_app(app, logging)

    # tornado logs 2xx/3xx at INFO, 4xx at WARNING, and 5xx at ERROR
    assert not tornado_access_logger.isEnabledFor(logging.INFO)
    assert tornado_access_logger.isEnabledFor(logging.WARNING)


def test_setup_logger_keeps_kombu_at_info_when_logging_to_file(monkeypatch: pytest.MonkeyPatch) -> None:
    app = Flask("kombu_file_logger_test")
    app.config.update(
        ENV_IDENTIFIER="non_local",
        SPIFFWORKFLOW_BACKEND_EVENT_STREAM_HOST=None,
        SPIFFWORKFLOW_BACKEND_LOG_LEVEL="debug",
        SPIFFWORKFLOW_BACKEND_LOG_TO_FILE=True,
        SPIFFWORKFLOW_BACKEND_LOGGERS_TO_USE="",
    )
    kombu_logger = logging.getLogger("kombu.pidbox")
    other_logger = logging.getLogger("some.library")
    for logger in (kombu_logger, other_logger):
        monkeypatch.setattr(logger, "handlers", [])
        monkeypatch.setattr(logger, "level", logger.level)
        monkeypatch.setattr(logger, "propagate", logger.propagate)
    monkeypatch.setattr(logging.root.manager, "loggerDict", {kombu_logger.name: kombu_logger, other_logger.name: other_logger})
    file_handler = logging.StreamHandler()
    primary_logger = SimpleNamespace(FileHandler=lambda _path: file_handler, root=logging.root)

    setup_logger_for_app(app, primary_logger)

    assert kombu_logger.level == logging.INFO
    assert other_logger.level == logging.DEBUG
    assert file_handler.level == logging.DEBUG


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


class _RecordCollector(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


@pytest.mark.parametrize("analytics_enabled", [True, False])
@pytest.mark.parametrize("log_level", ["info", "warning"])
@pytest.mark.parametrize("log_to_file", [True, False])
@pytest.mark.parametrize("celery_worker", [True, False])
@pytest.mark.parametrize("flask_debug", [True, False])
def test_setup_routes_event_details_to_output_and_analytics(
    monkeypatch: pytest.MonkeyPatch,
    analytics_enabled: bool,
    log_level: str,
    log_to_file: bool,
    celery_worker: bool,
    flask_debug: bool,
) -> None:
    # Exercise real logger routing, not a replacement handler on spiff.event.
    monkeypatch.setattr(logging.root.manager, "loggerDict", {})
    root_collector = _RecordCollector()
    monkeypatch.setattr(logging.root, "handlers", [root_collector])
    monkeypatch.setattr(logging.root, "level", logging.WARNING)
    monkeypatch.setattr(LoggingService, "_spiff_logger", logging.getLogger("spiff.event"))
    if celery_worker:
        monkeypatch.setenv("SPIFFWORKFLOW_BACKEND_RUNNING_IN_CELERY_WORKER", "true")
    else:
        monkeypatch.delenv("SPIFFWORKFLOW_BACKEND_RUNNING_IN_CELERY_WORKER", raising=False)

    stdout, original_stdout, file_output = io.StringIO(), io.StringIO(), io.StringIO()
    monkeypatch.setattr(sys, "stdout", stdout)
    monkeypatch.setattr(sys, "__stdout__", original_stdout)
    monkeypatch.setattr(logging, "FileHandler", lambda _path: logging.StreamHandler(file_output))
    analytics_events: list[dict] = []

    def collect_analytics(handler: SpiffLogHandler, record: logging.LogRecord) -> None:
        # Keep the real filter and wire format; replace only delivery to the socket.
        analytics_events.append(json.loads(handler.format(record)))

    monkeypatch.setattr(SpiffLogHandler, "emit", collect_analytics)
    app = Flask("event_output_test")
    app.config.update(
        # Debug mode enables Flask's logger before Arena configures its routing.
        DEBUG=flask_debug,
        ENV_IDENTIFIER="non_local",
        SPIFFWORKFLOW_BACKEND_EVENT_STREAM_HOST="unused.invalid" if analytics_enabled else None,
        SPIFFWORKFLOW_BACKEND_EVENT_STREAM_PORT=1234,
        SPIFFWORKFLOW_BACKEND_EVENT_STREAM_SOURCE="test",
        SPIFFWORKFLOW_BACKEND_LOG_LEVEL=log_level,
        SPIFFWORKFLOW_BACKEND_LOG_TO_FILE=log_to_file,
        SPIFFWORKFLOW_BACKEND_LOGGERS_TO_USE="",
    )
    setup_logger_for_app(app, logging, force_run_with_celery=celery_worker)
    if not analytics_enabled:
        # Reconfiguration must not duplicate the output handler.
        setup_logger_for_app(app, logging, force_run_with_celery=celery_worker)

    details = {
        "process_instance_id": 6635,
        "task_spec": "Activity_One",
        "metadata": {"color": "blue"},
        "error_info": {"line_number": 3},
    }
    with app.app_context():
        g.user = SimpleNamespace(id=7, username="kb")
        LoggingService.log_event("task_completed", details)

    output = file_output if log_to_file else original_stdout if celery_worker else stdout
    records = [json.loads(line) for line in output.getvalue().splitlines()]
    if log_level == "info":
        (record,) = records
        assert record.items() >= details.items()
        assert record["message"] == "task_completed"
        assert record["loggerName"] == "spiff.event"
    else:
        assert records == []
    for unused_output in (stdout, original_stdout, file_output):
        if unused_output is not output:
            assert unused_output.getvalue() == ""
    assert root_collector.records == []
    if analytics_enabled:
        (event,) = analytics_events
        assert event["type"] == "spiff.event"
        assert event["data"].items() >= details.items()
        assert event["data"]["username"] == "kb"
    else:
        assert analytics_events == []
    for handler in logging.getLogger("spiff").handlers:
        handler.close()
