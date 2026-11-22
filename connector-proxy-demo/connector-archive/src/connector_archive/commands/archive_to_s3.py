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


class ArchiveToS3(ConnectorCommand):
    """Write a summary PDF, the uploaded files, and a manifest for one process run to an S3 bucket.

    Credentials come from the parameters, so use secret references (for example 'secret:archive_aws_secret_access_key').
    The object keys are the same each time for the same key_prefix, so a retry replaces a partial archive.
    manifest.json is deleted after the first upload and written last. If it is present, the archive is complete.
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
            # The deadline is only checked between objects, so stop a stalled request well before the backend gives up.
            config=Config(connect_timeout=5, read_timeout=15, retries={"max_attempts": 2, "mode": "standard"}),
        )

    def execute(self, _config: Any, _task_data: Any) -> ConnectorProxyResponseDict:
        error: CommandErrorDict | None = None
        body: dict[str, Any] = {}
        logs: list[str] = []
        try:
            started_at = time.monotonic()
            entries = build_archive_entries(self.report, self.files, self.key_prefix)
            client = self._s3_client()
            manifest_entry = entries[-1]
            for index, entry in enumerate(entries):
                if time.monotonic() - started_at > UPLOAD_DEADLINE_IN_SECONDS:
                    raise TimeoutError(
                        f"Stopped after {UPLOAD_DEADLINE_IN_SECONDS} seconds before {entry.key}. The archive is not "
                        "complete. Retry the task."
                    )
                client.put_object(
                    Bucket=self.bucket,
                    Key=entry.key,
                    Body=entry.body,
                    ContentType=entry.content_type,
                    Metadata={"sha256": entry.sha256},
                )
                if index == 0:
                    # A retry can have fewer or different files. Remove the old manifest so it never describes them.
                    # This runs after the first upload works, so a wrong bucket or key keeps an earlier complete archive.
                    client.delete_object(Bucket=self.bucket, Key=manifest_entry.key)
                logs.append(f"archived s3://{self.bucket}/{entry.key} ({entry.size} bytes)")
            body = {
                "bucket": self.bucket,
                "key_prefix": manifest_entry.key.rsplit("/", 1)[0],
                "manifest_key": manifest_entry.key,
                "summary_key": entries[-2].key,
                "file_count": len(entries) - 2,
                "objects": [{"key": e.key, "size": e.size, "sha256": e.sha256} for e in entries],
            }
        except (ArchiveInputError, ReportPdfError) as exception:
            error = {"error_code": "ArchiveInvalidInput", "message": str(exception)}
        except ClientError as exception:
            # ClientError messages hold the S3 error code and the operation, never the credentials.
            error = {
                "error_code": "ArchiveUploadFailed",
                "message": f"S3 rejected the upload to bucket '{self.bucket}': {exception}",
            }
        except TimeoutError as exception:
            error = {"error_code": "ArchiveUploadFailed", "message": str(exception)}
        except BotoCoreError as exception:
            error = {"error_code": "ArchiveUploadFailed", "message": f"Could not upload to bucket '{self.bucket}': {exception}"}

        return {
            "command_response": {"body": body, "mimetype": "application/json"},
            "error": error,
            "command_response_version": 2,
            "spiff__logs": logs,
        }
