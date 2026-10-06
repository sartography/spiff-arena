import json
import logging
import os
import select
import socket
import time
import warnings
from collections.abc import Callable
from socket import SocketIO
from threading import Event
from threading import Thread
from threading import current_thread
from typing import Any
from typing import cast
from unittest.mock import patch

import pytest
from flask.app import Flask
from prometheus_client import REGISTRY

from spiffworkflow_backend.services.logging_service import EVENT_STREAM_ACK_PROTOCOL_LINE
from spiffworkflow_backend.services.logging_service import EVENT_STREAM_PENDING_EVENTS
from spiffworkflow_backend.services.logging_service import SpiffLogHandler
from spiffworkflow_backend.services.logging_service import configure_event_stream_socket

Behavior = Callable[[SocketIO, list[bytes]], None]


def event_record(data: dict[str, Any] | None = None) -> logging.LogRecord:
    record = logging.LogRecord(
        name="spiff.event",
        level=logging.INFO,
        pathname=__file__,
        lineno=0,
        msg="task_completed",
        args=(),
        exc_info=None,
    )
    record.__dict__["_spiff_data"] = data if data is not None else {"process_instance_id": 123}
    return record


def event_id(line: bytes) -> str:
    return str(json.loads(line)["id"])


def wait_until(predicate: Callable[[], bool], timeout: float = 5) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return predicate()


def negotiate(stream: SocketIO) -> None:
    assert stream.readline() == EVENT_STREAM_ACK_PROTOCOL_LINE
    stream.write(b"READY\n")


def acknowledge(count: int, release: Event | None = None) -> Behavior:
    def behavior(stream: SocketIO, lines: list[bytes]) -> None:
        negotiate(stream)
        for _ in range(count):
            line = stream.readline()
            if not line:
                return
            lines.append(line)
        if release is not None:
            release.wait(timeout=5)
        stream.write(b"".join(f"ACK {event_id(line)}\n".encode() for line in lines))
        stream.readline()

    return behavior


def read_then_close(count: int, negotiated: bool = True) -> Behavior:
    def behavior(stream: SocketIO, lines: list[bytes]) -> None:
        if negotiated:
            negotiate(stream)
        for _ in range(count):
            lines.append(stream.readline())

    return behavior


def reject_first(count: int) -> Behavior:
    def behavior(stream: SocketIO, lines: list[bytes]) -> None:
        negotiate(stream)
        for index in range(count):
            line = stream.readline()
            lines.append(line)
            stream.write(b"NACK invalid-event\n" if index == 0 else f"ACK {event_id(line)}\n".encode())
        stream.readline()

    return behavior


def acknowledge_after_full_window(window: int, total: int, release: Event) -> Behavior:
    def behavior(stream: SocketIO, lines: list[bytes]) -> None:
        negotiate(stream)
        for _ in range(window):
            lines.append(stream.readline())
        release.wait(timeout=5)
        stream.write(b"".join(f"ACK {event_id(line)}\n".encode() for line in lines))
        while len(lines) < total:
            line = stream.readline()
            if not line:
                return
            lines.append(line)
            stream.write(f"ACK {event_id(line)}\n".encode())
        stream.readline()

    return behavior


def acknowledge_some_then_close(count: int, acknowledged: int) -> Behavior:
    def behavior(stream: SocketIO, lines: list[bytes]) -> None:
        negotiate(stream)
        for _ in range(count):
            lines.append(stream.readline())
        stream.write(b"".join(f"ACK {event_id(line)}\n".encode() for line in lines[:acknowledged]))

    return behavior


def acknowledge_until_closed() -> Behavior:
    def behavior(stream: SocketIO, lines: list[bytes]) -> None:
        negotiate(stream)
        while line := stream.readline():
            lines.append(line)
            stream.write(f"ACK {event_id(line)}\n".encode())

    return behavior


def hold_without_acknowledging(count: int) -> Behavior:
    def behavior(stream: SocketIO, lines: list[bytes]) -> None:
        negotiate(stream)
        for _ in range(count):
            lines.append(stream.readline())
        while stream.readline():
            pass

    return behavior


class FakeListener:
    """Accept one connection per scripted behavior and record the lines each connection received."""

    def __init__(self, behaviors: list[Behavior]) -> None:
        self.server = socket.create_server(("127.0.0.1", 0))
        self.server.settimeout(5)
        self.address = self.server.getsockname()
        self.behaviors = behaviors
        self.connections: list[list[bytes]] = []
        self.thread = Thread(target=self.run, daemon=True)
        self.thread.start()

    def run(self) -> None:
        for behavior in self.behaviors:
            try:
                connection, _ = self.server.accept()
            except OSError:
                return
            with connection:
                connection.settimeout(5)
                lines: list[bytes] = []
                self.connections.append(lines)
                try:
                    behavior(connection.makefile("rwb", buffering=0), lines)
                except OSError:
                    pass

    def close(self) -> None:
        self.server.close()
        self.thread.join(timeout=5)


def connected_handler(app: Flask, address: tuple[str, int] | None) -> SpiffLogHandler:
    handler = SpiffLogHandler(app)
    if address is not None:
        handler.host, handler.port = address
        handler.address = address
    return handler


def acknowledged_handler(app: Flask, address: tuple[str, int] | None = None) -> SpiffLogHandler:
    handler = connected_handler(app, address)
    handler.ack_enabled = True
    handler.ack_timeout_seconds = 2
    handler.retry_interval_seconds = 0.01
    handler.retryStart = 0.01
    handler.shutdown_drain_seconds = 2
    return handler


def emit_without_delivery(handler: SpiffLogHandler, count: int) -> list[str]:
    with patch.object(handler, "start_retry_thread"):
        for _ in range(count):
            handler.emit(event_record())
    return [event_id(payload) for payload in handler.pending_events]


def close_in_forked_child(handler: SpiffLogHandler) -> int:
    with warnings.catch_warnings():
        # Python 3.12+ warns about forking a process that has other threads.
        warnings.simplefilter("ignore", DeprecationWarning)
        pid = os.fork()
    if pid == 0:
        exit_code = 1
        try:
            handler.close()
            exit_code = 0
        finally:
            os._exit(exit_code)
    _, status = os.waitpid(pid, 0)
    return os.waitstatus_to_exitcode(status)


def peer_received_data(peer: socket.socket) -> bool:
    readable, _, _ = select.select([peer], [], [], 0.2)
    return bool(readable)


class TestEventStreamDelivery:
    def test_acknowledged_emit_does_no_socket_work(self, app: Flask) -> None:
        handler = acknowledged_handler(app)
        with (
            patch.object(handler, "makeSocket", side_effect=AssertionError("emit opened a socket")) as make_socket,
            patch.object(handler, "start_retry_thread") as start_retry_thread,
        ):
            handler.emit(event_record())

        make_socket.assert_not_called()
        start_retry_thread.assert_called_once()
        assert len(handler.pending_events) == 1
        assert REGISTRY.get_sample_value("spiff_event_stream_pending_events") == 1
        handler.pending_events.clear()
        handler.close()

    def test_acknowledged_sender_removes_events_only_after_ack(self, app: Flask) -> None:
        release = Event()
        listener = FakeListener([acknowledge(3, release)])
        handler = acknowledged_handler(app, listener.address)
        try:
            ids = emit_without_delivery(handler, 3)
            handler.start_retry_thread()

            assert wait_until(lambda: bool(listener.connections) and len(listener.connections[0]) == 3)
            assert handler.pending_event_count() == 3
            release.set()
            assert wait_until(lambda: handler.pending_event_count() == 0)
            assert [event_id(line) for line in listener.connections[0]] == ids
        finally:
            handler.close()
            listener.close()

    def test_acknowledged_sender_resends_unacknowledged_events_in_order_after_disconnect(self, app: Flask) -> None:
        listener = FakeListener([read_then_close(2), acknowledge(2)])
        handler = acknowledged_handler(app, listener.address)
        try:
            ids = emit_without_delivery(handler, 2)
            handler.start_retry_thread()

            assert wait_until(lambda: handler.pending_event_count() == 0)
            assert [[event_id(line) for line in lines] for lines in listener.connections] == [ids, ids]
        finally:
            handler.close()
            listener.close()

    def test_acknowledged_sender_drops_and_reports_a_rejected_event(self, app: Flask) -> None:
        listener = FakeListener([reject_first(2)])
        handler = acknowledged_handler(app, listener.address)
        rejected_before = REGISTRY.get_sample_value("spiff_event_stream_rejected_events_total") or 0
        try:
            with patch.object(app.logger, "error") as error:
                ids = emit_without_delivery(handler, 2)
                handler.start_retry_thread()
                assert wait_until(lambda: handler.pending_event_count() == 0)

            error.assert_called_once()
            extras = error.call_args.kwargs["extra"]["extras"]
            assert extras["event_id"] == ids[0]
            assert extras["rejection_reason"] == "invalid-event"
            assert REGISTRY.get_sample_value("spiff_event_stream_rejected_events_total") == rejected_before + 1
        finally:
            handler.close()
            listener.close()

    def test_acknowledged_sender_reconnects_when_listener_stops_acknowledging(self, app: Flask) -> None:
        listener = FakeListener([hold_without_acknowledging(1), acknowledge(1)])
        handler = acknowledged_handler(app, listener.address)
        handler.ack_timeout_seconds = 0.2
        try:
            ids = emit_without_delivery(handler, 1)
            handler.start_retry_thread()

            assert wait_until(lambda: handler.pending_event_count() == 0)
            assert [[event_id(line) for line in lines] for lines in listener.connections] == [ids, ids]
        finally:
            handler.close()
            listener.close()

    def test_acknowledged_close_delivers_buffered_events(self, app: Flask) -> None:
        listener = FakeListener([acknowledge(2)])
        handler = acknowledged_handler(app, listener.address)
        try:
            ids = emit_without_delivery(handler, 2)

            handler.close()

            assert handler.pending_event_count() == 0
            assert [event_id(line) for line in listener.connections[0]] == ids
        finally:
            listener.close()

    def test_acknowledged_sender_waits_at_a_full_window_until_acknowledged(self, app: Flask) -> None:
        release = Event()
        listener = FakeListener([acknowledge_after_full_window(3, 7, release)])
        handler = acknowledged_handler(app, listener.address)
        handler.ack_window = 3
        try:
            ids = emit_without_delivery(handler, 7)
            handler.start_retry_thread()

            assert wait_until(lambda: bool(listener.connections) and len(listener.connections[0]) == 3)
            # Give the sender time to overrun the window if it were going to.
            time.sleep(0.2)
            with handler.state_lock:
                assert [event_id(payload) for _id, payload in handler.unacknowledged_events] == ids[:3]
                assert [event_id(payload) for payload in handler.pending_events] == ids[3:]
            assert len(listener.connections[0]) == 3

            release.set()
            assert wait_until(lambda: handler.pending_event_count() == 0)
            assert [event_id(line) for line in listener.connections[0]] == ids
        finally:
            handler.close()
            listener.close()

    def test_acknowledged_sender_resends_only_unacknowledged_events_after_partial_progress(self, app: Flask) -> None:
        listener = FakeListener([acknowledge_some_then_close(4, 2), acknowledge(2)])
        handler = acknowledged_handler(app, listener.address)
        try:
            ids = emit_without_delivery(handler, 4)
            handler.start_retry_thread()

            assert wait_until(lambda: handler.pending_event_count() == 0)
            assert [[event_id(line) for line in lines] for lines in listener.connections] == [ids, ids[2:]]
        finally:
            handler.close()
            listener.close()

    def test_acknowledged_sender_keeps_concurrent_events_while_reconnecting(self, app: Flask) -> None:
        thread_count = 4
        events_per_thread = 25
        listener = FakeListener([read_then_close(5), read_then_close(0, negotiated=False), acknowledge_until_closed()])
        handler = acknowledged_handler(app, listener.address)

        def emit_sequence(thread_index: int) -> None:
            for sequence in range(events_per_thread):
                handler.emit(event_record({"thread": thread_index, "sequence": sequence}))
                time.sleep(0.002)

        try:
            emitters = [Thread(target=emit_sequence, args=(index,)) for index in range(thread_count)]
            for emitter in emitters:
                emitter.start()
            for emitter in emitters:
                emitter.join(timeout=5)

            total = thread_count * events_per_thread
            assert wait_until(lambda: len(listener.connections) == 3 and len(listener.connections[2]) == total)
            assert wait_until(lambda: handler.pending_event_count() == 0)
            delivered = listener.connections[2]
            assert len({event_id(line) for line in delivered}) == total
            assert listener.connections[0] == delivered[:5]
            assert listener.connections[1] == []
            data = [json.loads(line)["data"] for line in delivered]
            for thread_index in range(thread_count):
                sequences = [item["sequence"] for item in data if item["thread"] == thread_index]
                assert sequences == list(range(events_per_thread))
        finally:
            handler.close()
            listener.close()

    def test_pending_gauge_matches_queue_when_emit_races_a_drain(self, app: Flask) -> None:
        handler = acknowledged_handler(app)
        sender_side, peer = socket.socketpair()
        handler.sock = cast(socket.socket | None, sender_side)
        emitter_computed_depth = Event()
        resume_emitter = Event()
        publish = EVENT_STREAM_PENDING_EVENTS.set

        def emit() -> None:
            handler.emit(event_record())

        emitter = Thread(target=emit)

        def pause_emitter_before_publishing(value: float) -> None:
            if current_thread() is emitter and not emitter_computed_depth.is_set():
                emitter_computed_depth.set()
                resume_emitter.wait(timeout=5)
            publish(value)

        def drain() -> None:
            handler.send_acknowledged_window()
            handler.handle_acknowledgement(f"ACK {handler.unacknowledged_events[0][0]}".encode())
            handler.update_pending_metric()

        try:
            with (
                patch.object(EVENT_STREAM_PENDING_EVENTS, "set", side_effect=pause_emitter_before_publishing),
                patch.object(handler, "start_retry_thread"),
            ):
                emitter.start()
                assert emitter_computed_depth.wait(timeout=5)
                drainer = Thread(target=drain)
                drainer.start()
                drainer.join(timeout=0.2)
                resume_emitter.set()
                emitter.join(timeout=5)
                drainer.join(timeout=5)

            assert handler.pending_event_count() == 0
            assert REGISTRY.get_sample_value("spiff_event_stream_pending_events") == 0
        finally:
            resume_emitter.set()
            handler.close()
            peer.close()

    def test_legacy_sender_reconnects_after_listener_closes_connection(self, app: Flask) -> None:
        listener = FakeListener([read_then_close(1, negotiated=False), read_then_close(1, negotiated=False)])
        handler = connected_handler(app, listener.address)
        try:
            assert handler.send(b'{"id":"first"}\n')
            assert wait_until(lambda: listener.connections == [[b'{"id":"first"}\n']])
            # Let the listener's close reach the client before the next write.
            time.sleep(0.2)

            assert handler.send(b'{"id":"second"}\n')

            assert wait_until(lambda: len(listener.connections) == 2 and len(listener.connections[1]) == 1)
            assert listener.connections == [[b'{"id":"first"}\n'], [b'{"id":"second"}\n']]
        finally:
            handler.close()
            listener.close()

    def test_child_process_discards_inherited_connection_and_buffer(self, app: Flask) -> None:
        handler = acknowledged_handler(app)
        inherited, peer = socket.socketpair()
        handler.sock = cast(socket.socket | None, inherited)
        handler.pending_events.append(b'{"id":"parent-pending"}\n')
        handler.unacknowledged_events.append(("parent-sent", b'{"id":"parent-sent"}\n'))
        handler.owner_pid = -1

        handler.reset_after_fork_if_needed()

        assert handler.sock is None
        assert handler.pending_event_count() == 0
        assert handler.retry_thread is None
        assert handler.owner_pid == os.getpid()
        peer.close()
        handler.close()

    @pytest.mark.skipif(not hasattr(os, "fork"), reason="requires os.fork")
    def test_acknowledged_forked_child_that_only_closes_leaves_parent_connection_alone(self, app: Flask) -> None:
        handler = acknowledged_handler(app)
        inherited, peer = socket.socketpair()
        handler.sock = cast(socket.socket | None, inherited)
        try:
            parent_ids = emit_without_delivery(handler, 1)

            assert close_in_forked_child(handler) == 0

            assert not peer_received_data(peer)
            peer.settimeout(5)
            stream = peer.makefile("rwb", buffering=0)
            handler.emit(event_record())
            lines = [stream.readline(), stream.readline()]
            assert event_id(lines[0]) == parent_ids[0]
            stream.write(b"".join(f"ACK {event_id(line)}\n".encode() for line in lines))
            assert wait_until(lambda: handler.pending_event_count() == 0)
        finally:
            handler.close()
            peer.close()

    @pytest.mark.skipif(not hasattr(os, "fork"), reason="requires os.fork")
    def test_legacy_forked_child_that_only_closes_leaves_parent_connection_alone(self, app: Flask) -> None:
        handler = connected_handler(app, None)
        handler.retry_interval_seconds = 0.01
        handler.shutdown_drain_seconds = 2
        inherited, peer = socket.socketpair()
        handler.sock = cast(socket.socket | None, inherited)
        parent_payload = handler.makePickle(event_record())
        handler.pending_events.append(parent_payload)
        try:
            assert close_in_forked_child(handler) == 0

            assert not peer_received_data(peer)
            peer.settimeout(5)
            stream = peer.makefile("rb", buffering=0)
            handler.emit(event_record())
            lines = [stream.readline(), stream.readline()]
            assert lines[0] == parent_payload
            assert wait_until(lambda: handler.pending_event_count() == 0)
        finally:
            handler.close()
            peer.close()

    def test_event_stream_socket_detects_dead_peers(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            configure_event_stream_socket(sock)

            assert sock.getsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE) != 0
            if hasattr(socket, "TCP_USER_TIMEOUT"):
                assert sock.getsockopt(socket.IPPROTO_TCP, socket.TCP_USER_TIMEOUT) == 30_000
