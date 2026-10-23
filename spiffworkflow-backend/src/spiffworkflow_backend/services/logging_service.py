import contextlib
import json
import logging
import os
import random
import select
import socket
import sys
import time
import weakref
from collections import deque
from logging.handlers import SocketHandler
from threading import Event
from threading import RLock
from threading import Thread
from threading import current_thread
from typing import Any
from uuid import uuid4

from flask import g
from flask.app import Flask
from prometheus_client import Counter
from prometheus_client import Gauge

SPIFF_LOG_HANDLER_SKIP_RECORD_ATTR = "spiff_log_handler_skip_record"
EVENT_STREAM_PAUSE_FILE = "/tmp/spiff-event-stream-paused"  # noqa: S108 - container-local operator control marker
EVENT_STREAM_RETRY_INTERVAL_SECONDS = 1.0
EVENT_STREAM_SHUTDOWN_DRAIN_SECONDS = 5.0
EVENT_STREAM_ACK_PROTOCOL_LINE = b"SPIFF-ANALYTICS/2\n"
EVENT_STREAM_MAX_PROTOCOL_LINE_BYTES = 512
# Short receive waits let the sender interleave new events with outstanding
# acknowledgements; the ACK timeout still bounds a listener that stops progressing.
EVENT_STREAM_ACK_POLL_SECONDS = 0.05
EVENT_STREAM_TCP_OPTIONS = (
    ("TCP_KEEPIDLE", 30),
    ("TCP_KEEPINTVL", 10),
    ("TCP_KEEPCNT", 3),
    # Without this, writes to a vanished peer succeed locally for ~15 minutes of retransmits.
    ("TCP_USER_TIMEOUT", 30_000),
)

# In multiprocess mode, prometheus_client opens this process's metric file as
# soon as an unlabeled metric is defined. Every entry point imports this module
# (bin/wait_for_db_to_be_ready.py, Celery, apscheduler) before create_app or
# boot_server_in_docker creates the directory.
if prometheus_multiproc_dir := os.environ.get("PROMETHEUS_MULTIPROC_DIR"):
    os.makedirs(prometheus_multiproc_dir, exist_ok=True)

EVENT_STREAM_PENDING_EVENTS = Gauge(
    "spiff_event_stream_pending_events",
    "Analytics events buffered or awaiting listener acknowledgement in this process.",
    multiprocess_mode="livesum",
)
EVENT_STREAM_REJECTED_EVENTS_TOTAL = Counter(
    "spiff_event_stream_rejected_events_total",
    "Analytics events the listener permanently rejected.",
)


class EventStreamProtocolError(ConnectionError):
    pass


def configure_event_stream_socket(sock: socket.socket) -> None:
    if sock.family not in (socket.AF_INET, socket.AF_INET6):
        return
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    for option_name, value in EVENT_STREAM_TCP_OPTIONS:
        option = getattr(socket, option_name, None)
        if option is None:
            continue
        with contextlib.suppress(OSError):
            sock.setsockopt(socket.IPPROTO_TCP, option, value)


def event_stream_peer_has_closed(sock: socket.socket) -> bool:
    """Detect a peer that closed or reset an otherwise idle connection without blocking."""
    try:
        if hasattr(select, "poll"):
            poller = select.poll()
            poller.register(sock, select.POLLIN)
            if not poller.poll(0):
                return False
        else:
            readable, _, _ = select.select([sock], [], [], 0)
            if not readable:
                return False
        return sock.recv(1, socket.MSG_PEEK) == b""
    except (OSError, ValueError):
        return True


# flask logging formats:
#   from: https://www.askpython.com/python-modules/flask/flask-logging
# %(asctime)s— The timestamp as a string.
# %(levelname)s—The logging level as a string.
# %(name)s—The logger name as a string.
# %(threadname)s—The thread name as a string.
# %(message)s—The log message.


class InvalidLogLevelError(Exception):
    pass


def skip_apscheduler_running_job_record(record: logging.LogRecord) -> bool:
    return not record.getMessage().startswith("Running job ")


# Container health checks and Prometheus may scrape these every few seconds. Failures still log.
SUCCESSFUL_PROBE_PATHS = {"/api/v1.0/status", "/metrics"}


def skip_successful_probe_access_record(record: logging.LogRecord) -> bool:
    # uvicorn access records carry (client_addr, method, path_with_query, http_version, status_code)
    if not isinstance(record.args, tuple) or len(record.args) != 5:
        return True
    _client_addr, method, path_with_query, _http_version, status_code = record.args
    path = str(path_with_query).split("?", 1)[0]
    is_success = isinstance(status_code, int) and 200 <= status_code < 300
    return not (method == "GET" and path in SUCCESSFUL_PROBE_PATHS and is_success)


EVENT_STREAM_HANDLERS: "weakref.WeakSet[SpiffLogHandler]" = weakref.WeakSet()


def reset_event_stream_handlers_after_fork() -> None:
    for handler in list(EVENT_STREAM_HANDLERS):
        handler.reset_after_fork_if_needed()


if hasattr(os, "register_at_fork"):
    os.register_at_fork(after_in_child=reset_event_stream_handlers_after_fork)


class SpiffLogHandler(SocketHandler):
    def __init__(self, app: Flask, *args: Any) -> None:
        super().__init__(
            app.config["SPIFFWORKFLOW_BACKEND_EVENT_STREAM_HOST"],
            app.config["SPIFFWORKFLOW_BACKEND_EVENT_STREAM_PORT"],
        )
        self.app = app
        # Guards both queues and the pending gauge so every gauge write reflects the
        # queue state at that moment. Network I/O must stay outside this lock.
        self.state_lock = RLock()
        self.pending_events: deque[bytes] = deque()
        self.retry_stop = Event()
        self.retry_wakeup = Event()
        self.retry_thread: Thread | None = None
        self.pause_file = EVENT_STREAM_PAUSE_FILE
        self.retry_interval_seconds = EVENT_STREAM_RETRY_INTERVAL_SECONDS
        self.shutdown_drain_seconds = EVENT_STREAM_SHUTDOWN_DRAIN_SECONDS
        self.delivery_failure_count = 0
        self.next_socket_warning_at = 0.0
        self.ack_enabled = bool(app.config.get("SPIFFWORKFLOW_BACKEND_EVENT_STREAM_ACK_ENABLED", False))
        self.ack_timeout_seconds = float(app.config.get("SPIFFWORKFLOW_BACKEND_EVENT_STREAM_ACK_TIMEOUT_SECONDS", 30))
        self.ack_window = max(int(app.config.get("SPIFFWORKFLOW_BACKEND_EVENT_STREAM_ACK_WINDOW", 100)), 1)
        self.unacknowledged_events: deque[tuple[str, bytes]] = deque()
        self.ack_buffer = bytearray()
        self.last_ack_progress_at = 0.0
        self.owner_pid = os.getpid()
        try:
            self.socket_warning_interval_seconds = int(
                os.environ.get("SPIFFWORKFLOW_BACKEND_EVENT_STREAM_WARNING_INTERVAL_SECONDS", "60")
            )
        except ValueError:
            self.socket_warning_interval_seconds = 60
        if self.socket_warning_interval_seconds < 1:
            self.socket_warning_interval_seconds = 60
        EVENT_STREAM_HANDLERS.add(self)

    def format(self, record: Any) -> str:
        return json.dumps(
            {
                "version": "1.0",
                "type": record.name,
                "id": str(uuid4()),
                "source": self.app.config["SPIFFWORKFLOW_BACKEND_EVENT_STREAM_SOURCE"],
                "timestamp": time.time(),
                "data": record._spiff_data,
            }
        )

    def get_user_info(self) -> tuple[int | None, str | None]:
        try:
            return g.user.id, g.user.username
        except Exception:
            return None, None

    def get_default_process_info(self) -> tuple[int | None, str | None]:
        try:
            tld = self.app.config["THREAD_LOCAL_DATA"]
            return tld.process_instance_id, tld.process_model_identifier
        except Exception:
            return None, None

    def filter(self, record: Any) -> bool:
        if getattr(record, SPIFF_LOG_HANDLER_SKIP_RECORD_ATTR, False):
            return False

        if (
            record.name == "spiff.task"
            and record.task_type
            in ("SubWorkflowTask", "CallActivity", "StandardLoopTask", "ParallelMultiInstanceTask", "SequentialMultiInstanceTask")
            and record.state == "READY"
        ):
            return False

        if record.name.startswith("spiff"):
            user_id, user_name = self.get_user_info()
            data = {
                "message": record.msg,
                "userid": user_id,
                "username": user_name,
                "process_instance_id": getattr(record, "process_instance_id", None),
                "process_model_identifier": getattr(record, "process_model_identifier", None),
            }

            process_instance_id, process_model_identifier = self.get_default_process_info()
            if data["process_instance_id"] is None:
                data["process_instance_id"] = process_instance_id
            if data["process_model_identifier"] is None:
                data["process_model_identifier"] = process_model_identifier

            if record.name == "spiff.task":
                properties = [
                    "workflow_spec",
                    "task_spec",
                    "task_id",
                    "task_type",
                    "state",
                    "last_state_change",
                    "elapsed",
                    "parent",
                ]
            elif record.name == "spiff.workflow":
                properties = ["workflow_spec", "completed", "success", "parent_task_id", "root"]
            elif record.name == "spiff.data":
                properties = ["workflow_spec", "task_spec", "task_id", "task_type"]
            elif record.name == "spiff.event":
                properties = ["bpmn_name", "milestone", "task_id", "task_spec", "metadata", "error_info"]
            else:
                properties = []

            for attr in properties:
                if hasattr(record, attr):
                    data[attr] = getattr(record, attr)
                    if not (data[attr] is None or isinstance(data[attr], dict)):
                        data[attr] = str(data[attr])
            record._spiff_data = data

            return True
        else:
            return False

    def makePickle(self, record: Any) -> bytes:  # noqa: N802
        # Instead of returning a pickled log record, write the json entry to the socket
        return (self.format(record) + "\n").encode("utf-8")

    def makeSocket(self, timeout: float = 1) -> socket.socket:  # noqa: N802
        sock = super().makeSocket(timeout)
        configure_event_stream_socket(sock)
        return sock

    def pending_event_count(self) -> int:
        with self.state_lock:
            return len(self.pending_events) + len(self.unacknowledged_events)

    def update_pending_metric(self) -> None:
        with self.state_lock:
            EVENT_STREAM_PENDING_EVENTS.set(self.pending_event_count())

    def reset_after_fork_if_needed(self) -> None:
        """Discard connection, buffer, and lock state copied from a parent process."""
        pid = os.getpid()
        if pid == self.owner_pid:
            return
        self.owner_pid = pid
        # A parent thread may have held these locks at fork time and does not exist in the child.
        self.state_lock = RLock()
        self.retry_stop = Event()
        self.retry_wakeup = Event()
        self.retry_thread = None
        if self.sock is not None:
            # Closing only the child's descriptor leaves the parent's connection open;
            # shutdown() would tear down the shared connection.
            with contextlib.suppress(OSError):
                self.sock.close()
            self.sock = None
        self.pending_events.clear()
        self.unacknowledged_events.clear()
        self.ack_buffer.clear()
        self.retryTime = None

    def schedule_reconnect(self, jitter: bool = False) -> None:
        if self.retryTime is None:
            self.retryPeriod = self.retryStart
        else:
            self.retryPeriod = min(self.retryPeriod * self.retryFactor, self.retryMax)
        delay = self.retryPeriod * random.uniform(0.5, 1.0) if jitter else self.retryPeriod  # noqa: S311
        self.retryTime = time.time() + delay

    def createSocket(self, record: Any | None = None) -> None:  # noqa: N802
        now = time.time()
        if self.retryTime is None:
            attempt = True
        else:
            attempt = now >= self.retryTime
        if attempt:
            try:
                self.sock = self.makeSocket()
                self.retryTime = None
            except OSError as exception:
                self.schedule_reconnect()
                self.log_socket_failure(exception, record)
        elif record is not None:
            self.log_socket_failure(None, record)

    def send(self, s: bytes, record: Any | None = None) -> bool:  # type: ignore[override]
        if self.sock is not None and event_stream_peer_has_closed(self.sock):
            # A listener that restarted closed this connection. Writing would
            # succeed locally and the event would be lost.
            self.sock.close()
            self.sock = None
        if self.sock is None:
            self.createSocket(record)
        if self.sock:
            try:
                self.sock.sendall(s)
                return True
            except OSError as exception:
                self.sock.close()
                self.sock = None
                self.log_socket_failure(exception, record)
        return False

    def emit(self, record: Any) -> None:
        try:
            self.reset_after_fork_if_needed()
            s = self.makePickle(record)
            with self.state_lock:
                queue_was_empty = not self.pending_events
                self.pending_events.append(s)
                self.update_pending_metric()
            if self.ack_enabled:
                # The request or task thread never touches the socket; the sender thread delivers.
                self.start_retry_thread()
                return
            self.flush_pending(max_events=1, record=record if queue_was_empty else None)
            if self.pending_events:
                self.start_retry_thread()
        except Exception:
            self.handleError(record)

    def delivery_is_paused(self) -> bool:
        return bool(self.pause_file) and os.path.exists(self.pause_file)

    def flush_pending(self, max_events: int | None = None, record: Any | None = None) -> None:
        if self.delivery_is_paused():
            if self.sock is not None:
                self.sock.close()
                self.sock = None
            return

        sent = 0
        while self.pending_events and (max_events is None or sent < max_events):
            payload = self.pending_events[0]
            if not self.send(payload, record):
                break
            with self.state_lock:
                self.pending_events.popleft()
            record = None
            sent += 1
        self.update_pending_metric()

    def start_retry_thread(self) -> None:
        # Emitters and close() can race here; two senders would interleave writes and acknowledgements.
        with self.state_lock:
            if self.retry_thread is None or not self.retry_thread.is_alive():
                self.retry_thread = Thread(
                    target=self.retry_pending_events,
                    daemon=True,
                    name="spiff-event-stream-retry",
                )
                self.retry_thread.start()
            self.retry_wakeup.set()

    def retry_pending_events(self) -> None:
        while not self.retry_stop.is_set():
            if self.ack_enabled:
                if self.pending_event_count() and self.deliver_acknowledged():
                    continue
                self.update_pending_metric()
                self.retry_wakeup.wait(self.retry_interval_seconds)
                self.retry_wakeup.clear()
                continue
            self.retry_wakeup.wait(self.retry_interval_seconds)
            self.retry_wakeup.clear()
            if self.retry_stop.is_set():
                return
            self.acquire()
            try:
                self.flush_pending()
            finally:
                self.release()

    def deliver_acknowledged(self) -> bool:
        """Run one send and receive step. Return False when the sender should wait before retrying."""
        if self.delivery_is_paused():
            self.drop_acknowledged_connection()
            return False
        if self.sock is None:
            self.connect_acknowledged()
            if self.sock is None:
                return False
        try:
            self.send_acknowledged_window()
            if self.unacknowledged_events:
                self.receive_acknowledgements()
        except OSError as exception:
            self.drop_acknowledged_connection()
            self.schedule_reconnect(jitter=True)
            self.log_socket_failure(exception, None)
            return False
        finally:
            self.update_pending_metric()
        return True

    def connect_acknowledged(self) -> None:
        if self.retryTime is not None and time.time() < self.retryTime:
            return
        sock: socket.socket | None = None
        try:
            sock = self.makeSocket(timeout=self.ack_timeout_seconds)
            sock.settimeout(self.ack_timeout_seconds)
            sock.sendall(EVENT_STREAM_ACK_PROTOCOL_LINE)
            self.ack_buffer.clear()
            reply = self.read_protocol_line(sock)
            if reply != b"READY":
                raise EventStreamProtocolError("event stream listener did not accept acknowledged delivery")
        except OSError as exception:
            if sock is not None:
                sock.close()
            self.ack_buffer.clear()
            self.schedule_reconnect(jitter=True)
            self.log_socket_failure(exception, None)
            return
        self.sock = sock
        self.retryTime = None
        self.last_ack_progress_at = time.monotonic()

    def read_protocol_line(self, sock: socket.socket) -> bytes:
        while b"\n" not in self.ack_buffer:
            chunk = sock.recv(EVENT_STREAM_MAX_PROTOCOL_LINE_BYTES)
            if not chunk:
                raise EventStreamProtocolError("event stream listener closed the connection during negotiation")
            self.ack_buffer.extend(chunk)
            if len(self.ack_buffer) > EVENT_STREAM_MAX_PROTOCOL_LINE_BYTES and b"\n" not in self.ack_buffer:
                raise EventStreamProtocolError("event stream listener sent an oversized protocol line")
        line, _, rest = bytes(self.ack_buffer).partition(b"\n")
        self.ack_buffer[:] = rest
        return line

    def send_acknowledged_window(self) -> None:
        if self.sock is None:
            raise EventStreamProtocolError("event stream socket is not connected")
        batch: list[bytes] = []
        invalid_payloads: list[bytes] = []
        with self.state_lock:
            while self.pending_events and len(self.unacknowledged_events) < self.ack_window:
                payload = self.pending_events.popleft()
                try:
                    event_id = str(json.loads(payload)["id"])
                except (ValueError, KeyError, TypeError):
                    invalid_payloads.append(payload)
                    continue
                if not self.unacknowledged_events:
                    self.last_ack_progress_at = time.monotonic()
                self.unacknowledged_events.append((event_id, payload))
                batch.append(payload)
            self.update_pending_metric()
        for payload in invalid_payloads:
            self.reject_event(None, payload, "event has no id")
        if batch:
            self.sock.settimeout(self.ack_timeout_seconds)
            self.sock.sendall(b"".join(batch))

    def receive_acknowledgements(self) -> None:
        if self.sock is None:
            raise EventStreamProtocolError("event stream socket is not connected")
        self.sock.settimeout(EVENT_STREAM_ACK_POLL_SECONDS)
        try:
            chunk = self.sock.recv(64 * 1024)
        except TimeoutError:
            if time.monotonic() - self.last_ack_progress_at > self.ack_timeout_seconds:
                raise TimeoutError(
                    f"event stream listener sent no acknowledgement for {self.ack_timeout_seconds:g} seconds"
                ) from None
            return
        if not chunk:
            raise EventStreamProtocolError("event stream listener closed the connection with unacknowledged events")
        self.ack_buffer.extend(chunk)
        while b"\n" in self.ack_buffer:
            line, _, rest = bytes(self.ack_buffer).partition(b"\n")
            self.ack_buffer[:] = rest
            self.handle_acknowledgement(line)
        if len(self.ack_buffer) > EVENT_STREAM_MAX_PROTOCOL_LINE_BYTES:
            raise EventStreamProtocolError("event stream listener sent an oversized protocol line")

    def handle_acknowledgement(self, line: bytes) -> None:
        with self.state_lock:
            if not self.unacknowledged_events:
                raise EventStreamProtocolError("event stream listener replied with no event awaiting acknowledgement")
            event_id, payload = self.unacknowledged_events[0]
            rejected = line.startswith(b"NACK ")
            if line != f"ACK {event_id}".encode() and not rejected:
                raise EventStreamProtocolError("event stream listener sent an acknowledgement out of order")
            self.unacknowledged_events.popleft()
            self.update_pending_metric()
        if rejected:
            self.reject_event(event_id, payload, line[5:].decode("utf-8", errors="replace"))
        self.last_ack_progress_at = time.monotonic()

    def reject_event(self, event_id: str | None, payload: bytes, reason: str) -> None:
        EVENT_STREAM_REJECTED_EVENTS_TOTAL.inc()
        event_type = None
        with contextlib.suppress(ValueError, AttributeError):
            event_type = json.loads(payload).get("type")
        self.app.logger.error(
            "Event stream listener permanently rejected a Spiff event; dropping it.",
            extra={
                SPIFF_LOG_HANDLER_SKIP_RECORD_ATTR: True,
                "extras": {"event_id": event_id, "event_type": event_type, "rejection_reason": reason},
            },
        )

    def drop_acknowledged_connection(self) -> None:
        if self.sock is not None:
            with contextlib.suppress(OSError):
                self.sock.close()
            self.sock = None
        self.ack_buffer.clear()
        with self.state_lock:
            if self.unacknowledged_events:
                # Resend in the original order; the listener's receipt ledger drops duplicates.
                self.pending_events.extendleft(reversed([payload for _event_id, payload in self.unacknowledged_events]))
                self.unacknowledged_events.clear()
                self.update_pending_metric()

    def close_acknowledged(self) -> None:
        deadline = time.monotonic() + self.shutdown_drain_seconds
        if self.pending_event_count() and not self.delivery_is_paused():
            # Shutdown is the last chance to deliver, so skip reconnect backoff.
            self.retryTime = None
            self.start_retry_thread()
            while self.pending_event_count() and time.monotonic() < deadline:
                time.sleep(EVENT_STREAM_ACK_POLL_SECONDS)
        self.retry_stop.set()
        self.retry_wakeup.set()
        sender = self.retry_thread
        if sender is not None and sender is not current_thread():
            sender.join(timeout=1)
        if sender is None or not sender.is_alive():
            self.drop_acknowledged_connection()
        if self.pending_event_count():
            self.app.logger.error(
                "Event stream handler closed with unacknowledged events still pending.",
                extra={
                    SPIFF_LOG_HANDLER_SKIP_RECORD_ATTR: True,
                    "extras": {"pending_event_count": self.pending_event_count()},
                },
            )

    def close(self) -> None:
        # A forked child that never emitted must not drain the parent's events over the parent's connection.
        self.reset_after_fork_if_needed()
        if self.ack_enabled:
            self.close_acknowledged()
            super().close()
            return
        deadline = time.monotonic() + self.shutdown_drain_seconds
        self.acquire()
        try:
            while self.pending_events and not self.delivery_is_paused():
                # A process shutdown is the last opportunity to hand buffered
                # events to a healthy listener, so bypass normal reconnect backoff.
                self.retryTime = None
                self.flush_pending()
                if not self.pending_events or time.monotonic() >= deadline:
                    break
                time.sleep(min(self.retry_interval_seconds, max(deadline - time.monotonic(), 0)))
            if self.pending_events:
                self.app.logger.error(
                    "Event stream handler closed with buffered events still pending.",
                    extra={
                        SPIFF_LOG_HANDLER_SKIP_RECORD_ATTR: True,
                        "extras": {"pending_event_count": len(self.pending_events)},
                    },
                )
        finally:
            self.release()
        self.retry_stop.set()
        self.retry_wakeup.set()
        super().close()

    def log_socket_failure(self, exception: OSError | None, record: Any | None) -> None:
        self.delivery_failure_count += 1
        now = time.monotonic()
        if now < self.next_socket_warning_at:
            return

        delivery_failure_count = self.delivery_failure_count
        self.delivery_failure_count = 0
        self.next_socket_warning_at = now + self.socket_warning_interval_seconds

        spiff_data = getattr(record, "_spiff_data", {}) if record is not None else {}
        self.app.logger.warning(
            "Event stream socket logging failed; retaining Spiff event records for retry.",
            extra={
                SPIFF_LOG_HANDLER_SKIP_RECORD_ATTR: True,
                "extras": {
                    "event_stream_host": self.host,
                    "event_stream_port": self.port,
                    "delivery_failure_count": delivery_failure_count,
                    "pending_event_count": self.pending_event_count(),
                    "event_logger_name": getattr(record, "name", None),
                    "event_message": getattr(record, "msg", None),
                    "process_instance_id": spiff_data.get("process_instance_id"),
                    "process_model_identifier": spiff_data.get("process_model_identifier"),
                    "task_id": spiff_data.get("task_id"),
                    "task_spec": spiff_data.get("task_spec"),
                    "socket_error": str(exception) if exception is not None else "retry backoff active",
                },
            },
        )


class TextFormatter(logging.Formatter):
    """Formatter for reading logs in a terminal, with the extras that JsonFormatter adds as fields at the end."""

    def formatMessage(self, record: logging.LogRecord) -> str:  # noqa: N802, this is overriding a method from python's stdlib
        message = super().formatMessage(record)
        extras = record.__dict__.get("extras")
        if extras:
            message += " " + " ".join(f"{key}={json.dumps(value, default=str)}" for key, value in extras.items())
        return message


# originally from https://stackoverflow.com/a/70223539/6090676


class JsonFormatter(logging.Formatter):
    """Formatter that outputs JSON strings after parsing the LogRecord.

    @param dict fmt_dict: Key: logging format attribute pairs. Defaults to {"message": "message"}.
    @param str time_format: time.strftime() format string. Default: "%Y-%m-%dT%H:%M:%S"
    @param str msec_format: Microsecond formatting. Appended at the end. Default: "%s.%03dZ"
    """

    def __init__(
        self,
        fmt_dict: dict | None = None,
        time_format: str = "%Y-%m-%dT%H:%M:%S",
        msec_format: str = "%s.%03dZ",
    ):
        self.fmt_dict = fmt_dict if fmt_dict is not None else {"message": "message"}
        self.default_time_format = time_format
        self.default_msec_format = msec_format
        self.datefmt = None

    def usesTime(self) -> bool:  # noqa: N802, this is overriding a method from python's stdlib
        """Overwritten to look for the attribute in the format dict values instead of the fmt string."""
        return "asctime" in self.fmt_dict.values()

    # we are overriding a method that returns a string and returning a dict, hence the Any
    def formatMessage(self, record: logging.LogRecord) -> Any:  # noqa: N802, this is overriding a method from python's stdlib
        """Overwritten to return a dictionary of the relevant LogRecord attributes instead of a string.

        KeyError is raised if an unknown attribute is provided in the fmt_dict.
        """
        return {fmt_key: record.__dict__[fmt_val] for fmt_key, fmt_val in self.fmt_dict.items()}

    def format(self, record: logging.LogRecord) -> str:
        """Mostly the same as the parent's class method.

        The difference being that a dict is manipulated and dumped as JSON instead of a string.
        """
        record.message = record.getMessage()

        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)

        message_dict = self.formatMessage(record)

        if record.exc_info:
            # Cache the traceback text to avoid converting it multiple times
            # (it's constant anyway)
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)

        if record.exc_text:
            message_dict["exc_info"] = record.exc_text

        if record.stack_info:
            message_dict["stack_info"] = self.formatStack(record.stack_info)

        if record.__dict__.get("extras"):
            message_dict = {**record.__dict__["extras"], **message_dict}

        return json.dumps(message_dict, default=str)


# Libraries too chatty for our logs, held at no lower than this level. Their child loggers inherit it.
# SPIFFWORKFLOW_BACKEND_LOGGERS_TO_USE turns the ERROR ones back on.
QUIET_LOGGERS = {
    "celery.redirected": logging.ERROR,
    "connexion": logging.ERROR,
    "flask_cors.core": logging.ERROR,
    "flask_cors.extension": logging.ERROR,
    "sqlalchemy": logging.ERROR,
    # every job run
    "apscheduler": logging.INFO,
    # dozens of lines on every worker start
    "celery.bootsteps": logging.INFO,
    # every Celery remote-control broadcast, e.g. Flower's enable_events every few seconds
    "kombu": logging.INFO,
    # every outbound connection, e.g. Sentry's session uploads every minute per process
    "urllib3": logging.INFO,
}


def skip_spiff_engine_record(record: logging.LogRecord) -> bool:
    # SpiffWorkflow logs every task state change for analytics. Only its warnings and errors belong in our logs.
    is_spiff_engine = record.name.split(".", 1)[0] == "spiff" and record.name != "spiff.event"
    return not (is_spiff_engine and record.levelno < logging.WARNING)


def setup_logger_for_app(app: Flask, force_run_with_celery: bool = False) -> None:
    """Send every logger through one root handler, and SpiffWorkflow records to analytics when configured."""
    # Celery workers set up logging from Celery's after_setup_logger signal instead (see celery_worker.py),
    # so that it runs after Celery configures its own logging.
    if os.environ.get("SPIFFWORKFLOW_BACKEND_RUNNING_IN_CELERY_WORKER") and not force_run_with_celery:
        return

    log_level_name = app.config["SPIFFWORKFLOW_BACKEND_LOG_LEVEL"].upper()
    log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if log_level_name not in log_levels:
        raise InvalidLogLevelError(f"Log level given is invalid: '{log_level_name}'. Valid options are {log_levels}")
    log_level: int = getattr(logging, log_level_name)

    if app.config["SPIFFWORKFLOW_BACKEND_LOG_TO_FILE"]:
        output_handler: logging.Handler = logging.FileHandler(f"{app.instance_path}/../../log/{app.config['ENV_IDENTIFIER']}.log")
    else:
        # Celery replaces sys.stdout with a proxy that logs prints; write to the real stdout.
        output_handler = logging.StreamHandler((sys.__stdout__ or sys.stdout) if force_run_with_celery else sys.stdout)
    output_handler.setFormatter(get_log_formatter(app))
    # A handler level as well as the root level, because spiff.event stays at INFO for analytics.
    output_handler.setLevel(log_level)
    output_handler.addFilter(skip_spiff_engine_record)

    spiff_logger = logging.getLogger("spiff")
    analytics_handler = next((handler for handler in spiff_logger.handlers if isinstance(handler, SpiffLogHandler)), None)

    # Flask creates app.logger on first use, and in debug mode it gets its own level and stderr handler.
    # Create it now so the reset below covers it.
    app.logger  # noqa: B018

    # Flask, gunicorn, uvicorn, Celery, and some libraries attach their own handlers.
    # Route every logger through the root handler instead, at the root level unless set below.
    for logger in list(logging.root.manager.loggerDict.values()):
        if isinstance(logger, logging.Logger):
            logger.handlers = []
            logger.propagate = True
            logger.setLevel(logging.NOTSET)
    for handler in logging.root.handlers:
        handler.close()
    logging.root.handlers = [output_handler]
    logging.root.setLevel(log_level)

    quiet_loggers = dict(QUIET_LOGGERS)
    loggers_to_use = app.config.get("SPIFFWORKFLOW_BACKEND_LOGGERS_TO_USE") or ""
    for logger_name in filter(None, loggers_to_use.split(",")):
        if quiet_loggers.get(logger_name) == logging.ERROR:
            del quiet_loggers[logger_name]
        else:
            app.logger.warning(
                f"Logger '{logger_name}' is not one of the quiet loggers that SPIFFWORKFLOW_BACKEND_LOGGERS_TO_USE turns on. "
                "You do not need to add it to SPIFFWORKFLOW_BACKEND_LOGGERS_TO_USE."
            )
    # even when turned on, sqlalchemy logs query results at DEBUG
    quiet_loggers.setdefault("sqlalchemy", logging.INFO)
    for logger_name, quiet_level in quiet_loggers.items():
        logging.getLogger(logger_name).setLevel(max(log_level, quiet_level))

    logging.getLogger("apscheduler.executors.default").addFilter(skip_apscheduler_running_job_record)
    logging.getLogger("uvicorn.access").addFilter(skip_successful_probe_access_record)

    # SpiffWorkflow logs under "spiff", and LoggingService.log_event under spiff.event.
    if app.config["SPIFFWORKFLOW_BACKEND_EVENT_STREAM_HOST"] is not None:
        spiff_logger.handlers = [analytics_handler or SpiffLogHandler(app)]
        spiff_logger.setLevel(logging.INFO)
    else:
        # Without analytics, skip building engine records that the output handler would drop.
        spiff_logger.setLevel(logging.WARNING)
    logging.getLogger("spiff.event").setLevel(logging.INFO)


def get_log_formatter(app: Flask) -> logging.Formatter:
    log_format = app.config["SPIFFWORKFLOW_BACKEND_LOG_FORMAT"]
    if log_format == "text":
        return TextFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    if log_format == "json":
        return JsonFormatter(
            {
                "level": "levelname",
                "message": "message",
                "loggerName": "name",
                "processName": "processName",
                "processID": "process",
                "threadName": "threadName",
                "threadID": "thread",
                "timestamp": "asctime",
            }
        )
    raise ValueError(f"Log format given is invalid: '{log_format}'. Valid options are ['json', 'text']")


class LoggingService:
    _spiff_logger = logging.getLogger("spiff.event")

    @classmethod
    def log_event(cls, message: str, log_extras: dict | None = None) -> None:
        log_extras = log_extras or {}
        # SpiffLogHandler reads the extras as record attributes, but JsonFormatter only writes "extras" to stdout
        cls._spiff_logger.info(message, extra={**log_extras, "extras": log_extras})
