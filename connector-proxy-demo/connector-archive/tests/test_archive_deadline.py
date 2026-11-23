import multiprocessing
import threading
import time
from http.server import BaseHTTPRequestHandler
from http.server import ThreadingHTTPServer
from typing import Any

import pytest

from connector_archive.commands.archive_to_s3 import ArchiveToS3


class BackoffArchiveToS3(ArchiveToS3):
    def _s3_client(self) -> Any:
        client = super()._s3_client()
        # Force an SDK backoff longer than the entire command budget.
        client.meta.events.register_first("needs-retry.s3", lambda **_kwargs: 60)
        return client


@pytest.mark.parametrize("stall", [None, "PUT", "DELETE", "late-delete", "retry", "backoff", "trickle"])
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

        def do_DELETE(self) -> None:  # noqa: N802
            self.handle_s3()

        def handle_s3(self) -> None:
            self.rfile.read(int(self.headers.get("Content-Length", 0)))
            requests.append((self.command, self.path))
            if stall == "late-delete" and self.command == "PUT":
                time.sleep(max(0, started + budget - 0.4 - time.monotonic()))
            if stall in ("retry", "backoff") and len(requests) == 1:
                self.send_response(500)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            if stall == self.command or stall == "retry" or (stall == "late-delete" and self.command == "DELETE"):
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
            self.send_response(200 if self.command == "PUT" else 204)
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
            assert [method for method, _ in requests] == ["PUT", "DELETE", "PUT"]
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
            assert not any(path.endswith("manifest.json") and method == "PUT" for method, path in requests)
            if stall in ("DELETE", "late-delete"):
                assert [method for method, _ in requests] == ["PUT", "DELETE"]
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
