import hashlib
import json
import multiprocessing
import socket
import time
from typing import Any

import boto3  # type: ignore
from botocore.config import Config  # type: ignore
from botocore.exceptions import BotoCoreError  # type: ignore
from botocore.exceptions import ClientError  # type: ignore
from spiffworkflow_connector_command.command_interface import CommandErrorDict
from spiffworkflow_connector_command.command_interface import ConnectorCommand
from spiffworkflow_connector_command.command_interface import ConnectorProxyResponseDict

from connector_archive.archive import ArchiveInputError
from connector_archive.archive import build_archive_entries
from connector_archive.report_pdf import ReportPdfError

# The backend waits CONNECTOR_PROXY_COMMAND_TIMEOUT (45 seconds) for a connector response. Stop before that so
# the backend gets this error and not a timeout while uploads continue in the proxy.
UPLOAD_DEADLINE_IN_SECONDS = 40


class ArchiveUploadError(ValueError):
    pass


def _timeout_message() -> str:
    return f"Stopped after {UPLOAD_DEADLINE_IN_SECONDS} seconds. The archive is not complete. Retry the task."


def _run_archive(command: "ArchiveToS3", deadline: float, connection: socket.socket) -> None:
    # A separate process can be stopped even during DNS, a socket write/read, or an SDK retry/backoff.
    with connection:
        payload = json.dumps(command._execute(deadline)).encode("utf-8")
        connection.sendall(len(payload).to_bytes(8, "big") + payload)


def _receive_response(connection: socket.socket, deadline: float) -> ConnectorProxyResponseDict:
    def read_exactly(size: int) -> bytes:
        chunks = []
        while size:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(_timeout_message())
            connection.settimeout(remaining)
            chunk = connection.recv(min(size, 64 * 1024))
            if not chunk:
                raise EOFError("Archive worker closed an incomplete response.")
            chunks.append(chunk)
            size -= len(chunk)
        return b"".join(chunks)

    # Read both the length prefix and the entire payload within one absolute deadline. Socket readiness
    # alone is insufficient: even a frame's length prefix can arrive in several writes.
    size = int.from_bytes(read_exactly(8), "big")
    payload = read_exactly(size)
    if time.monotonic() >= deadline:
        raise TimeoutError(_timeout_message())
    return json.loads(payload)


class ArchiveToS3(ConnectorCommand):
    """Write a summary PDF, the uploaded files, and a manifest for one process run to an S3 bucket.

    Credentials come from the parameters, so use secret references (for example 'secret:archive_aws_secret_access_key').
    The object keys are the same each time for the same key_prefix, so a retry replaces a partial archive.
    S3 versioning must remain enabled. manifest.json pins exact file/summary versions and is replaced last,
    so concurrent workers cannot mix archives. Readers must use the manifest's version_id with each key.
    A failed retry leaves the earlier complete manifest readable; concurrent publications are last-writer-wins.
    """

    def __init__(
        self,
        bucket: str,
        key_prefix: str,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        report: Any,
        files: Any = None,
        region: str = "us-east-1",
        endpoint_url: str | None = None,
    ):
        self.bucket = bucket
        self.key_prefix = key_prefix
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.report = report
        self.files = files
        self.region = region
        self.endpoint_url = endpoint_url or None

    def _s3_client(self) -> Any:
        return boto3.client(
            "s3",
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region,
            endpoint_url=self.endpoint_url,
            # These inactivity timeouts complement the supervisor's hard, command-wide deadline.
            config=Config(connect_timeout=5, read_timeout=15, retries={"max_attempts": 2, "mode": "standard"}),
        )

    def execute(self, _config: Any, _task_data: Any) -> ConnectorProxyResponseDict:
        deadline = time.monotonic() + UPLOAD_DEADLINE_IN_SECONDS
        # Do not fork a threaded proxy or share its sockets. Unlike a timed-out thread/future, this worker
        # can actually be stopped, bounding every S3 call and SDK retry to the remaining budget.
        context = multiprocessing.get_context("spawn")
        receiver, sender = socket.socketpair()
        worker = context.Process(target=_run_archive, args=(self, deadline, sender), daemon=True)
        message = _timeout_message()
        try:
            worker.start()
            sender.close()
            try:
                return _receive_response(receiver, deadline)
            except EOFError:
                message = "Archive worker stopped unexpectedly. The archive is not complete. Retry the task."
            except TimeoutError:
                pass
        finally:
            receiver.close()
            sender.close()
            if worker.pid is not None:
                if worker.is_alive():
                    worker.terminate()
                worker.join(timeout=1)
                if worker.is_alive():
                    worker.kill()
                    worker.join(timeout=1)
            if not worker.is_alive():
                worker.close()
        return {
            "command_response": {"body": {}, "mimetype": "application/json"},
            "error": {"error_code": "ArchiveUploadFailed", "message": message},
            "command_response_version": 2,
            "spiff__logs": [],
        }

    def _pin_legacy_manifest(self, client: Any, manifest_key: str) -> None:
        """Pin a pre-versioning-protocol archive before overwriting any of its fixed keys.

        Concurrent upgraders may publish different snapshots, but each is checksum-verified and immutable.
        Old connector workers must be stopped before adopting this protocol.
        """
        try:
            stored = client.get_object(Bucket=self.bucket, Key=manifest_key)
        except ClientError as exception:
            if exception.response["Error"]["Code"] in ("NoSuchKey", "404"):
                return
            raise
        try:
            with stored["Body"] as stream:
                manifest = json.loads(stream.read())
            if manifest["manifest_version"] == 2:
                return
            if manifest["manifest_version"] != 1:
                raise ArchiveUploadError("Unsupported existing archive manifest version.")
            for item in [*manifest["files"], manifest["summary"]]:
                key = item.get("archive_key", item.get("key"))
                obj = client.get_object(Bucket=self.bucket, Key=key)
                version_id = obj.get("VersionId")
                if not version_id:
                    obj["Body"].close()
                    # Pre-versioning objects can omit the header. Verify that the explicit null version exists;
                    # never assume a missing header on an S3-compatible service identifies a readable version.
                    obj = client.get_object(Bucket=self.bucket, Key=key, VersionId="null")
                    version_id = "null"
                with obj["Body"] as stream:
                    contents = stream.read()
                if len(contents) != item["size"] or hashlib.sha256(contents).hexdigest() != item["sha256"]:
                    raise ArchiveUploadError("The existing archive is inconsistent; restore it before retrying.")
                item["version_id"] = version_id
            manifest["manifest_version"] = 2
            contents = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8")
        except (KeyError, TypeError, ValueError) as exception:
            raise ArchiveUploadError(f"Could not pin the existing archive: {exception}") from exception
        client.put_object(
            Bucket=self.bucket,
            Key=manifest_key,
            Body=contents,
            ContentType="application/json",
            Metadata={"sha256": hashlib.sha256(contents).hexdigest()},
        )

    def _execute(self, deadline: float) -> ConnectorProxyResponseDict:
        error: CommandErrorDict | None = None
        body: dict[str, Any] = {}
        logs: list[str] = []
        try:
            entries = build_archive_entries(self.report, self.files, self.key_prefix)
            client = self._s3_client()
            manifest_entry = entries[-1]
            if client.get_bucket_versioning(Bucket=self.bucket).get("Status") != "Enabled":
                raise ArchiveUploadError("S3 bucket versioning must be enabled and remain enabled for archive retries.")
            self._pin_legacy_manifest(client, manifest_entry.key)
            versions: list[str] = []
            for entry in entries:
                if entry is manifest_entry:
                    manifest = json.loads(entry.body)
                    manifest["manifest_version"] = 2
                    for item, version_id in zip(manifest["files"], versions[:-1], strict=True):
                        item["version_id"] = version_id
                    manifest["summary"]["version_id"] = versions[-1]
                    entry.body = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8")
                    entry.sha256 = hashlib.sha256(entry.body).hexdigest()
                if time.monotonic() >= deadline:
                    raise TimeoutError(_timeout_message())
                uploaded = client.put_object(
                    Bucket=self.bucket,
                    Key=entry.key,
                    Body=entry.body,
                    ContentType=entry.content_type,
                    Metadata={"sha256": entry.sha256},
                )
                version_id = uploaded.get("VersionId")
                if not version_id or version_id == "null":
                    raise ArchiveUploadError("S3 did not return an immutable VersionId. Keep bucket versioning enabled.")
                versions.append(version_id)
                logs.append(f"archived s3://{self.bucket}/{entry.key} ({entry.size} bytes)")
            body = {
                "bucket": self.bucket,
                "key_prefix": manifest_entry.key.rsplit("/", 1)[0],
                "manifest_key": manifest_entry.key,
                "summary_key": entries[-2].key,
                "manifest_version_id": versions[-1],
                "summary_version_id": versions[-2],
                "file_count": len(entries) - 2,
                "objects": [
                    {"key": e.key, "size": e.size, "sha256": e.sha256, "version_id": v}
                    for e, v in zip(entries, versions, strict=True)
                ],
            }
        except (ArchiveInputError, ReportPdfError) as exception:
            error = {"error_code": "ArchiveInvalidInput", "message": str(exception)}
        except ClientError as exception:
            # ClientError messages hold the S3 error code and the operation, never the credentials.
            error = {
                "error_code": "ArchiveUploadFailed",
                "message": f"S3 rejected the upload to bucket '{self.bucket}': {exception}",
            }
        except (TimeoutError, ArchiveUploadError) as exception:
            error = {"error_code": "ArchiveUploadFailed", "message": str(exception)}
        except BotoCoreError as exception:
            error = {"error_code": "ArchiveUploadFailed", "message": f"Could not upload to bucket '{self.bucket}': {exception}"}

        return {
            "command_response": {"body": body, "mimetype": "application/json"},
            "error": error,
            "command_response_version": 2,
            "spiff__logs": logs,
        }
