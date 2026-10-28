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
from typing import Any

import pytest
from flask import Flask
from flask import g

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


class LoggingOutput:
    def __init__(self) -> None:
        self.stdout = io.StringIO()
        self.stderr = io.StringIO()
        self.celery_stdout = io.StringIO()
        self.file = io.StringIO()
        self.analytics: list[dict] = []
        self.app = Flask("isolated_logging_test")

    def lines(self, stream: io.StringIO) -> list[str]:
        return stream.getvalue().splitlines()

    def messages(self, stream: io.StringIO) -> list[str]:
        return [json.loads(line)["message"] for line in self.lines(stream)]


def setup_isolated_logging(
    monkeypatch: pytest.MonkeyPatch,
    log_level: str = "debug",
    analytics_enabled: bool = False,
    log_to_file: bool = False,
    celery_worker: bool = False,
    loggers_to_use: str = "",
    flask_debug: bool = False,
    log_format: str = "json",
    before_setup: Any = None,
) -> LoggingOutput:
    # A fresh logger hierarchy under the real root, so setup sees only the loggers a test creates.
    monkeypatch.setattr(logging.root.manager, "loggerDict", {})
    monkeypatch.setattr(logging.root, "handlers", [])
    monkeypatch.setattr(logging.root, "level", logging.WARNING)
    monkeypatch.setattr(LoggingService, "_spiff_logger", logging.getLogger("spiff.event"))

    output = LoggingOutput()
    monkeypatch.setattr(sys, "stdout", output.stdout)
    monkeypatch.setattr(sys, "stderr", output.stderr)
    monkeypatch.setattr(sys, "__stdout__", output.celery_stdout)
    monkeypatch.setattr(logging, "FileHandler", lambda _path: logging.StreamHandler(output.file))

    def collect_analytics(handler: SpiffLogHandler, record: logging.LogRecord) -> None:
        # Keep the real filter and wire format; replace only delivery to the socket.
        output.analytics.append(json.loads(handler.format(record)))

    monkeypatch.setattr(SpiffLogHandler, "emit", collect_analytics)
    output.app.config.update(
        DEBUG=flask_debug,
        ENV_IDENTIFIER="non_local",
        SPIFFWORKFLOW_BACKEND_EVENT_STREAM_HOST="unused.invalid" if analytics_enabled else None,
        SPIFFWORKFLOW_BACKEND_EVENT_STREAM_PORT=1234,
        SPIFFWORKFLOW_BACKEND_EVENT_STREAM_SOURCE="test",
        SPIFFWORKFLOW_BACKEND_LOG_FORMAT=log_format,
        SPIFFWORKFLOW_BACKEND_LOG_LEVEL=log_level,
        SPIFFWORKFLOW_BACKEND_LOG_TO_FILE=log_to_file,
        SPIFFWORKFLOW_BACKEND_LOGGERS_TO_USE=loggers_to_use,
    )
    if before_setup is not None:
        before_setup()
    setup_logger_for_app(output.app, celery_worker=celery_worker)
    return output


# Depends on monkeypatch so this runs before monkeypatch restores the real logger hierarchy.
@pytest.fixture(autouse=True)
def close_analytics_handlers(monkeypatch: pytest.MonkeyPatch) -> Any:
    yield
    for handler in logging.getLogger("spiff").handlers:
        handler.close()


def test_setup_routes_every_logger_through_one_root_handler(monkeypatch: pytest.MonkeyPatch) -> None:
    library_handler_output = io.StringIO()

    def add_library_logger() -> None:
        # e.g. gunicorn, uvicorn, and Celery give their loggers their own handlers and stop propagation
        library_logger = logging.getLogger("library.with.handler")
        library_logger.addHandler(logging.StreamHandler(library_handler_output))
        library_logger.propagate = False
        library_logger.setLevel(logging.ERROR)

    output = setup_isolated_logging(monkeypatch, log_level="info", before_setup=add_library_logger)
    logging.getLogger("library.with.handler").info("from a library")
    logging.getLogger("created.after.setup").info("from a later logger")
    logging.getLogger("created.after.setup").debug("below the configured level")

    assert output.messages(output.stdout) == ["from a library", "from a later logger"]
    assert library_handler_output.getvalue() == ""


def test_setup_quiets_chatty_libraries_and_their_children(monkeypatch: pytest.MonkeyPatch) -> None:
    output = setup_isolated_logging(monkeypatch)
    for name in (
        "kombu.pidbox",
        "urllib3.connectionpool",
        "alembic.runtime.migration",
        "apscheduler.scheduler",
        "celery.bootsteps",
        "celery.pool",
        "celery.utils.functional",
    ):
        logging.getLogger(name).debug(f"{name} debug")
        logging.getLogger(name).info(f"{name} info")
    logging.getLogger("sqlalchemy.engine.Engine").warning("sqlalchemy warning")
    logging.getLogger("sqlalchemy.engine.Engine").error("sqlalchemy error")
    logging.getLogger("spiffworkflow_backend").debug("app debug")

    assert output.messages(output.stdout) == [
        "kombu.pidbox info",
        "urllib3.connectionpool info",
        "alembic.runtime.migration info",
        "apscheduler.scheduler info",
        "celery.bootsteps info",
        "celery.pool info",
        "celery.utils.functional info",
        "sqlalchemy error",
        "app debug",
    ]


def test_setup_skips_routine_apscheduler_job_records(monkeypatch: pytest.MonkeyPatch) -> None:
    output = setup_isolated_logging(monkeypatch)
    executor_logger = logging.getLogger("apscheduler.executors.default")
    job = "correlate message instances (trigger: interval[0:00:10], next run at: 2026-10-23 14:58:05 UTC)"
    executor_logger.info(f'Running job "{job}"')
    executor_logger.info(f'Job "{job}" executed successfully')
    executor_logger.warning(f'Run time of job "{job}" was missed by 0:00:03')
    executor_logger.error(f'Job "{job}" raised an exception')

    assert output.messages(output.stdout) == [
        f'Run time of job "{job}" was missed by 0:00:03',
        f'Job "{job}" raised an exception',
    ]


def test_loggers_to_use_turns_quiet_loggers_back_on(monkeypatch: pytest.MonkeyPatch) -> None:
    output = setup_isolated_logging(monkeypatch, loggers_to_use="sqlalchemy,connexion")
    logging.getLogger("connexion.operations").debug("connexion debug")
    # sqlalchemy logs query results at DEBUG, so it stays at INFO even when turned on
    logging.getLogger("sqlalchemy.engine.Engine").debug("sqlalchemy debug")
    logging.getLogger("sqlalchemy.engine.Engine").info("sqlalchemy info")

    assert output.messages(output.stdout) == ["connexion debug", "sqlalchemy info"]


def test_setup_applies_the_same_rules_to_the_log_file(monkeypatch: pytest.MonkeyPatch) -> None:
    output = setup_isolated_logging(monkeypatch, log_to_file=True)
    logging.getLogger("sqlalchemy.engine.Engine").info("sqlalchemy info")
    logging.getLogger("spiffworkflow_backend").debug("app debug")

    assert output.messages(output.file) == ["app debug"]
    assert output.stdout.getvalue() == ""


def test_setup_can_run_again_without_duplicating_output(monkeypatch: pytest.MonkeyPatch) -> None:
    # e.g. Celery sets up logging again in each pool process
    output = setup_isolated_logging(monkeypatch, analytics_enabled=True)
    analytics_handler = logging.getLogger("spiff").handlers[0]
    setup_logger_for_app(output.app)
    LoggingService.log_event("task_completed", {"process_instance_id": 1})

    assert logging.getLogger("spiff").handlers == [analytics_handler]
    assert output.messages(output.stdout) == ["task_completed"]
    assert len(output.analytics) == 1


def test_text_format_adds_extras_before_the_traceback(monkeypatch: pytest.MonkeyPatch) -> None:
    output = setup_isolated_logging(monkeypatch, log_format="text")
    try:
        raise ValueError("bad value")
    except ValueError:
        extras = {"process_instance_id": 6635, "task_spec": "Activity_One", "metadata": {"color": "blue"}}
        logging.getLogger("spiffworkflow_backend").exception("Task failed", extra={"extras": extras})

    first_line, *traceback_lines = output.lines(output.stdout)
    assert first_line.endswith(
        ' - spiffworkflow_backend - ERROR - Task failed process_instance_id=6635 task_spec="Activity_One" '
        'metadata={"color": "blue"}'
    )
    assert traceback_lines[0] == "Traceback (most recent call last):"
    assert traceback_lines[-1] == "ValueError: bad value"


def test_invalid_log_format_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(ValueError, match="Log format given is invalid: 'xml'"):
        setup_isolated_logging(monkeypatch, log_format="xml")


@pytest.mark.parametrize("analytics_enabled", [True, False])
@pytest.mark.parametrize("log_level", ["info", "warning"])
@pytest.mark.parametrize("log_to_file", [True, False])
def test_flask_debug_mode_follows_the_configured_log_level(
    monkeypatch: pytest.MonkeyPatch, analytics_enabled: bool, log_level: str, log_to_file: bool
) -> None:
    # In debug mode, Flask adds its own stderr handler if app.logger is first used after setup.
    output = setup_isolated_logging(
        monkeypatch, log_level=log_level, analytics_enabled=analytics_enabled, log_to_file=log_to_file, flask_debug=True
    )
    output.app.logger.debug("app debug")
    output.app.logger.info("app info")
    output.app.logger.warning("app warning")

    destination = output.file if log_to_file else output.stdout
    expected = ["app info", "app warning"] if log_level == "info" else ["app warning"]
    assert output.messages(destination) == expected
    assert output.stderr.getvalue() == ""


@pytest.mark.parametrize("analytics_enabled", [True, False])
@pytest.mark.parametrize("log_level", ["info", "warning"])
@pytest.mark.parametrize("log_to_file", [True, False])
@pytest.mark.parametrize("celery_worker", [True, False])
def test_setup_routes_event_details_to_output_and_analytics(
    monkeypatch: pytest.MonkeyPatch,
    analytics_enabled: bool,
    log_level: str,
    log_to_file: bool,
    celery_worker: bool,
) -> None:
    output = setup_isolated_logging(
        monkeypatch,
        log_level=log_level,
        analytics_enabled=analytics_enabled,
        log_to_file=log_to_file,
        celery_worker=celery_worker,
    )
    details = {
        "process_instance_id": 6635,
        "task_spec": "Activity_One",
        "metadata": {"color": "blue"},
        "error_info": {"line_number": 3},
    }
    with Flask("isolated_logging_test").app_context():
        g.user = SimpleNamespace(id=7, username="kb")
        LoggingService.log_event("task_completed", details)

    destination = output.file if log_to_file else output.celery_stdout if celery_worker else output.stdout
    records = [json.loads(line) for line in output.lines(destination)]
    if log_level == "info":
        (record,) = records
        assert record.items() >= details.items()
        assert record["message"] == "task_completed"
        assert record["loggerName"] == "spiff.event"
    else:
        assert records == []
    for unused_output in (output.stdout, output.celery_stdout, output.file):
        if unused_output is not destination:
            assert unused_output.getvalue() == ""
    if analytics_enabled:
        (event,) = output.analytics
        assert event["type"] == "spiff.event"
        assert event["data"].items() >= details.items()
        assert event["data"]["username"] == "kb"
    else:
        assert output.analytics == []


@pytest.mark.parametrize("analytics_enabled", [True, False])
def test_spiff_engine_records_go_to_analytics_and_only_their_warnings_to_output(
    monkeypatch: pytest.MonkeyPatch, analytics_enabled: bool
) -> None:
    output = setup_isolated_logging(monkeypatch, analytics_enabled=analytics_enabled)
    task_extras = {"task_type": "UserTask", "state": "COMPLETED", "task_spec": "Activity_One"}
    logging.getLogger("spiff.task").debug("State set to COMPLETED", extra=task_extras)
    logging.getLogger("spiff.task").info("State changed to COMPLETED", extra=task_extras)
    logging.getLogger("spiff.workflow").warning("engine warning")

    assert output.messages(output.stdout) == ["engine warning"]
    if analytics_enabled:
        assert [(event["type"], event["data"]["message"]) for event in output.analytics] == [
            ("spiff.task", "State changed to COMPLETED"),
            ("spiff.workflow", "engine warning"),
        ]
        assert output.analytics[0]["data"]["task_spec"] == "Activity_One"
    else:
        assert output.analytics == []


def test_spiff_log_handler_sends_records_from_any_spiff_logger(monkeypatch: pytest.MonkeyPatch) -> None:
    output = setup_isolated_logging(monkeypatch, analytics_enabled=True)
    logging.getLogger("spiff.dmn").info("decision evaluated")
    logging.getLogger("spiff").info("from the parent logger")

    assert [(event["type"], sorted(event["data"])) for event in output.analytics] == [
        ("spiff.dmn", ["message", "process_instance_id", "process_model_identifier", "userid", "username"]),
        ("spiff", ["message", "process_instance_id", "process_model_identifier", "userid", "username"]),
    ]
