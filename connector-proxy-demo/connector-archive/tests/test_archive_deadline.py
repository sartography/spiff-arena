import json
import multiprocessing
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler
from http.server import ThreadingHTTPServer
from typing import Any

import pytest

from connector_archive.commands.archive_to_s3 import ArchiveToS3
from connector_archive.commands.archive_to_s3 import _receive_response


def _send_incomplete_response(command: ArchiveToS3, _deadline: float, connection: socket.socket) -> None:
    with connection:
        frame = (100_000).to_bytes(8, "big") + b"{"
        connection.sendall(frame[:3] if command.report["mode"] == "header" else frame)
        command.report["sent"].set()
        for _ in range(200):
            if command.report["mode"] == "trickle":
                connection.sendall(b" ")
            time.sleep(0.05)


@pytest.mark.parametrize("mode", ["header", "payload", "trickle"])
def test_incomplete_worker_response_uses_the_command_deadline(mode: str, monkeypatch: pytest.MonkeyPatch) -> None:
    budget = 3
    monkeypatch.setattr("connector_archive.commands.archive_to_s3.UPLOAD_DEADLINE_IN_SECONDS", budget)
    monkeypatch.setattr("connector_archive.commands.archive_to_s3._run_archive", _send_incomplete_response)
    sent = multiprocessing.get_context("spawn").Event()
    command = ArchiveToS3(
        bucket="unused",
        key_prefix="archive/42",
        aws_access_key_id="testing",
        aws_secret_access_key="testing",
        report={"mode": mode, "sent": sent},
    )
    children_before = {child.pid for child in multiprocessing.active_children()}
    started = time.monotonic()
    result = command.execute({}, {})
    elapsed = time.monotonic() - started

    assert sent.is_set(), "The worker must send partial frame data before the deadline"
    assert budget - 0.1 <= elapsed < budget + 2
    assert result["error"]["error_code"] == "ArchiveUploadFailed"
    assert "Stopped after" in result["error"]["message"]
    assert result["command_response"]["body"] == {}
    assert {child.pid for child in multiprocessing.active_children()} == children_before


def test_receives_a_complete_fragmented_large_response_before_the_deadline() -> None:
    expected = {"command_response": {"body": {"value": "x" * 200_000}}, "error": None}
    payload = json.dumps(expected).encode("utf-8")
    frame = len(payload).to_bytes(8, "big") + payload
    # Keep the sender open after the frame: completion must not depend on EOF or worker exit.
    receiver, sender = socket.socketpair()
    with receiver, sender:

        def send_fragments() -> None:
            for fragment in (frame[:2], frame[2:7], frame[7:30], frame[30:]):
                sender.sendall(fragment)
                time.sleep(0.01)

        writer = threading.Thread(target=send_fragments, daemon=True)
        writer.start()
        try:
            assert _receive_response(receiver, time.monotonic() + 2) == expected
        finally:
            writer.join(timeout=1)
        assert not writer.is_alive()


@pytest.mark.parametrize("frame", [b"\x00", (100).to_bytes(8, "big") + b"{"])
def test_incomplete_response_eof_is_reported(frame: bytes) -> None:
    receiver, sender = socket.socketpair()
    with receiver, sender:
        sender.sendall(frame)
        sender.close()
        with pytest.raises(EOFError):
            _receive_response(receiver, time.monotonic() + 1)


class BackoffArchiveToS3(ArchiveToS3):
    def _s3_client(self) -> Any:
        client = super()._s3_client()
        # Force an SDK backoff longer than the entire command budget.
        client.meta.events.register_first("needs-retry.s3.PutObject", lambda **_kwargs: 60)
        return client


@pytest.mark.parametrize("stall", [None, "PUT", "manifest", "late-manifest", "retry", "backoff", "trickle"])
def test_supervisor_bounds_in_flight_requests_and_retries(stall: str | None, monkeypatch: pytest.MonkeyPatch) -> None:
    requests: list[tuple[str, str]] = []
    disconnected = threading.Event()
    release = threading.Event()
    budget = 3
    monkeypatch.setattr("connector_archive.commands.archive_to_s3.UPLOAD_DEADLINE_IN_SECONDS", budget)

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *_args: object) -> None:
            pass

        def do_PUT(self) -> None:  # noqa: N802
            self.handle_s3()

        def do_GET(self) -> None:  # noqa: N802
            versioning = self.path.endswith("?versioning")
            body = b"<VersioningConfiguration><Status>Enabled</Status></VersioningConfiguration>" if versioning else b""
            self.send_response(200 if versioning else 404)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def handle_s3(self) -> None:
            self.rfile.read(int(self.headers.get("Content-Length", 0)))
            requests.append((self.command, self.path))
            is_manifest = self.path.endswith("manifest.json")
            if stall == "late-manifest" and not is_manifest:
                time.sleep(max(0, started + budget - 0.4 - time.monotonic()))
            if stall in ("retry", "backoff") and len(requests) == 1:
                self.send_response(500)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            if stall == "PUT" or stall == "retry" or (stall in ("manifest", "late-manifest") and is_manifest):
                # A stalled response must be interrupted by the supervisor, not by the 15s read timeout.
                self.connection.settimeout(5)
                if self.connection.recv(1) == b"":
                    disconnected.set()
                self.close_connection = True
                return
            if stall == "trickle":
                # Inactivity timeouts cannot limit a response that keeps making progress.
                self.send_response(200)
                self.send_header("Content-Length", "1000")
                self.end_headers()
                while not release.wait(0.05):
                    try:
                        self.wfile.write(b" ")
                        self.wfile.flush()
                    except OSError:
                        disconnected.set()
                        break
                self.close_connection = True
                return
            self.send_response(200)
            self.send_header("x-amz-version-id", f"version-{len(requests)}")
            self.send_header("Content-Length", "0")
            self.end_headers()

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    children_before = {child.pid for child in multiprocessing.active_children()}
    try:
        command_class = BackoffArchiveToS3 if stall == "backoff" else ArchiveToS3
        command = command_class(
            bucket="test-archive-bucket",
            key_prefix="archive/42",
            aws_access_key_id="testing",
            aws_secret_access_key="testing",
            report={"title": "Test", "sections": []},
            endpoint_url=f"http://127.0.0.1:{server.server_port}",
        )
        # execute must also work from a proxy request thread, where SIGALRM is unavailable.
        results: list[dict] = []
        started = time.monotonic()
        caller = threading.Thread(target=lambda: results.append(command.execute({}, {})))
        caller.start()
        caller.join(timeout=budget + 2)
        assert not caller.is_alive()
        elapsed = time.monotonic() - started
        assert elapsed < budget + 2
        assert len(results) == 1
        result = results[0]
        if stall is None:
            assert result["error"] is None
            assert [method for method, _ in requests] == ["PUT", "PUT"]
            assert requests[-1][1].endswith("manifest.json")
        else:
            assert result["error"]["error_code"] == "ArchiveUploadFailed"
            assert "Retry the task" in result["error"]["message"]
            assert budget - 0.1 <= elapsed
            if stall != "backoff":
                assert disconnected.wait(1), "The worker must close the active S3 connection before returning"
            count = len(requests)
            time.sleep(0.2)
            assert len(requests) == count, "No upload or retry may continue after execute returns"
            if stall in ("manifest", "late-manifest"):
                assert [method for method, _ in requests] == ["PUT", "PUT"]
                assert requests[-1][1].endswith("manifest.json")
            else:
                assert not any(path.endswith("manifest.json") for _, path in requests)
            if stall == "retry":
                assert [method for method, _ in requests] == ["PUT", "PUT"]
            if stall == "backoff":
                assert [method for method, _ in requests] == ["PUT"]
        assert {child.pid for child in multiprocessing.active_children()} == children_before
    finally:
        release.set()
        server.shutdown()
        server.server_close()
        thread.join(timeout=1)
