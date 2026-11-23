import base64
import hashlib
import io
import json
import time
from unittest.mock import patch

import boto3
import pytest
from botocore.exceptions import ClientError
from moto import mock_aws
from pypdf import PdfReader

from connector_archive.archive import build_archive_entries
from connector_archive.archive import safe_filename
from connector_archive.commands.archive_to_s3 import ArchiveToS3

BUCKET = "test-archive-bucket"


def data_url(filename: str, contents: bytes, mimetype: str = "text/plain") -> str:
    return f"data:{mimetype};name={filename};base64,{base64.b64encode(contents).decode('ascii')}"


def report() -> dict:
    return {
        "title": "Project Accounting Provisions",
        "metadata": [["Process instance", 42], ["Submitted by", "Zoë Müller – GL"]],
        "sections": [
            {"heading": "Request", "rows": [["Accrual name", "Q3 provisions"], ["Total accrued", 1234567.5]]},
            {
                "heading": "Review history",
                "columns": ["Step", "Status", "Reviewer", "When", "Comment"],
                "rows": [["Supervisor", "Approved", "Sam", "2026-11-20 10:00:00", "Looks good"]],
                "column_widths": [12, 12, 24, 20, 32],
            },
            {"heading": "Notes", "text": "Free text note."},
        ],
    }


def pdf_text(pdf_bytes: bytes) -> str:
    return "\n".join(page.extract_text() for page in PdfReader(io.BytesIO(pdf_bytes)).pages)


def command(**kwargs: object) -> ArchiveToS3:
    params = {
        "bucket": BUCKET,
        "key_prefix": "/r2r/project-accounting-provisions/42/",
        "aws_access_key_id": "testing",
        "aws_secret_access_key": "testing",
        "report": report(),
        "files": [],
    }
    params.update(kwargs)
    return ArchiveToS3(**params)  # type: ignore[arg-type]


def run_archive(**kwargs: object) -> dict:
    # Exercise archive semantics in-process so moto state and injected failures remain visible.
    # The public execute() supervisor is tested separately with real HTTP requests.
    return command(**kwargs)._execute(time.monotonic() + 40)


@pytest.fixture
def s3():  # type: ignore[no-untyped-def]
    with mock_aws():
        client = boto3.client("s3", region_name="us-east-1")
        client.create_bucket(Bucket=BUCKET)
        yield client


def test_archives_files_pdf_and_manifest(s3) -> None:  # type: ignore[no-untyped-def]
    files = [
        {
            "id": 7,
            "filename": "calc.xlsx",
            "mimetype": "application/vnd.ms-excel",
            "digest": hashlib.sha256(b"first").hexdigest(),
            "created_at_in_seconds": 1763700000,
            "data_url": data_url("calc.xlsx", b"first"),
        },
        # Same name, different contents: both are kept.
        {"filename": "calc.xlsx", "data_url": data_url("calc.xlsx", b"second")},
        data_url("notes%20%26%20more.txt", b"plain string input"),
    ]
    result = run_archive(files=files)

    assert result["error"] is None
    body = result["command_response"]["body"]
    prefix = "r2r/project-accounting-provisions/42"
    assert body["manifest_key"] == f"{prefix}/manifest.json"
    assert body["file_count"] == 3
    keys = [o["key"] for o in body["objects"]]
    assert keys == [
        f"{prefix}/files/001-calc.xlsx",
        f"{prefix}/files/002-calc.xlsx",
        f"{prefix}/files/003-notes _ more.txt",
        f"{prefix}/summary.pdf",
        f"{prefix}/manifest.json",
    ]

    stored = s3.get_object(Bucket=BUCKET, Key=f"{prefix}/files/002-calc.xlsx")
    assert stored["Body"].read() == b"second"
    assert stored["Metadata"]["sha256"] == hashlib.sha256(b"second").hexdigest()
    assert s3.head_object(Bucket=BUCKET, Key=f"{prefix}/files/001-calc.xlsx")["ContentType"] == "application/vnd.ms-excel"

    manifest = json.loads(s3.get_object(Bucket=BUCKET, Key=f"{prefix}/manifest.json")["Body"].read())
    assert [f["original_filename"] for f in manifest["files"]] == ["calc.xlsx", "calc.xlsx", "notes & more.txt"]
    assert manifest["files"][0]["uploaded_at"] == "2025-11-21 04:40:00 UTC"
    summary_bytes = s3.get_object(Bucket=BUCKET, Key=f"{prefix}/summary.pdf")["Body"].read()
    assert manifest["summary"]["sha256"] == hashlib.sha256(summary_bytes).hexdigest()

    text = pdf_text(summary_bytes)
    for expected in [
        "Project Accounting Provisions",
        "Q3 provisions",
        "1,234,567.50",
        "Looks good",
        "Free text note.",
        "Archived files",
        "notes & more.txt",
        hashlib.sha256(b"second").hexdigest()[:20],
    ]:
        assert expected in text, expected


def test_unicode_text_survives_with_and_without_unicode_font(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    entries = build_archive_entries(report(), [], "a/b/1")
    # DejaVu is on the CI and Docker image; the text keeps its accents.
    with_font = pdf_text(entries[-2].body)
    # Without any unicode font, the PDF still renders; latin-1 accents survive and the dash becomes "-".
    monkeypatch.setenv("CONNECTOR_ARCHIVE_FONT_DIR", str(tmp_path))
    without_font = pdf_text(build_archive_entries(report(), [], "a/b/1")[-2].body)
    assert "Zoë Müller - GL" in without_font
    if "Zoë Müller – GL" not in with_font:
        pytest.skip("DejaVu fonts are not installed here")


def test_no_files_still_produces_a_complete_archive(s3) -> None:  # type: ignore[no-untyped-def]
    result = run_archive(files=None)
    assert result["error"] is None
    assert result["command_response"]["body"]["file_count"] == 0
    summary = s3.get_object(Bucket=BUCKET, Key="r2r/project-accounting-provisions/42/summary.pdf")["Body"].read()
    assert "No files were uploaded." in pdf_text(summary)


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"files": ["data:text/plain;name=a.txt;base64,spifffiledatadigest+" + "a" * 64]}, "digest reference"),
        ({"files": [{"digest": "0" * 64, "data_url": data_url("a.txt", b"x")}]}, "does not match its stored digest"),
        ({"files": ["not a data url"]}, "base64 data url"),
        ({"files": "data:text/plain;name=a.txt;base64,eA=="}, "files must be a list"),
        ({"key_prefix": "a/../b"}, "key_prefix"),
        ({"report": {"title": "x", "sections": [{"columns": ["a", "b"], "rows": [["only one"]]}]}}, "must have 2 values"),
        ({"report": {"title": "x", "sections": [{"columns": ["a", "b"], "rows": [], "column_widths": [1]}]}}, "column_widths"),
    ],
)
def test_invalid_input_is_reported_and_nothing_is_written(s3, kwargs: dict, message: str) -> None:  # type: ignore[no-untyped-def]
    result = run_archive(**kwargs)
    assert result["error"] is not None
    assert result["error"]["error_code"] == "ArchiveInvalidInput"
    assert message in result["error"]["message"]
    assert s3.list_objects_v2(Bucket=BUCKET).get("KeyCount") == 0


def test_upload_failure_is_reported_without_credentials(s3) -> None:  # type: ignore[no-untyped-def]
    result = run_archive(bucket="bucket-that-does-not-exist", aws_secret_access_key="super-secret-value")
    assert result["error"] is not None
    assert result["error"]["error_code"] == "ArchiveUploadFailed"
    assert "bucket-that-does-not-exist" in result["error"]["message"]
    assert "super-secret-value" not in json.dumps(result)


def test_retry_writes_the_same_keys(s3) -> None:  # type: ignore[no-untyped-def]
    files = [data_url("a.txt", b"a")]
    first = run_archive(files=files)
    second = run_archive(files=files)
    assert [o["key"] for o in first["command_response"]["body"]["objects"]] == [
        o["key"] for o in second["command_response"]["body"]["objects"]
    ]
    assert s3.list_objects_v2(Bucket=BUCKET)["KeyCount"] == 3


def test_failed_retry_removes_the_manifest_of_an_earlier_archive(s3) -> None:  # type: ignore[no-untyped-def]
    manifest_key = "r2r/project-accounting-provisions/42/manifest.json"
    assert run_archive(files=[data_url("a.txt", b"a")])["error"] is None
    assert s3.head_object(Bucket=BUCKET, Key=manifest_key)

    real_put_object = s3.put_object

    def put_object_that_fails_on_pdf(**kwargs):  # type: ignore[no-untyped-def]
        if kwargs["Key"].endswith("summary.pdf"):
            raise ClientError({"Error": {"Code": "InternalError", "Message": "boom"}}, "PutObject")
        return real_put_object(**kwargs)

    with patch.object(ArchiveToS3, "_s3_client", return_value=s3), patch.object(s3, "put_object", put_object_that_fails_on_pdf):
        result = run_archive(files=[data_url("b.txt", b"b")])

    assert result["error"] is not None
    assert result["error"]["error_code"] == "ArchiveUploadFailed"
    keys = [o["Key"] for o in s3.list_objects_v2(Bucket=BUCKET)["Contents"]]
    assert manifest_key not in keys


def test_failure_on_the_first_upload_keeps_an_earlier_complete_archive(s3) -> None:  # type: ignore[no-untyped-def]
    manifest_key = "r2r/project-accounting-provisions/42/manifest.json"
    assert run_archive(files=[data_url("a.txt", b"a")])["error"] is None

    def put_object_that_fails(**kwargs):  # type: ignore[no-untyped-def]
        raise ClientError({"Error": {"Code": "AccessDenied", "Message": "denied"}}, "PutObject")

    with patch.object(ArchiveToS3, "_s3_client", return_value=s3), patch.object(s3, "put_object", put_object_that_fails):
        result = run_archive(files=[data_url("b.txt", b"b")])

    assert result["error"]["error_code"] == "ArchiveUploadFailed"
    assert s3.head_object(Bucket=BUCKET, Key=manifest_key)


def test_stops_before_the_backend_times_out(s3, monkeypatch: pytest.MonkeyPatch) -> None:  # type: ignore[no-untyped-def]
    clock = iter([1.0, 2.0, 41.0])
    monkeypatch.setattr("connector_archive.commands.archive_to_s3.time.monotonic", lambda: next(clock))
    result = command(files=[data_url("a.txt", b"a"), data_url("b.txt", b"b")])._execute(40)

    assert result["error"] is not None
    assert result["error"]["error_code"] == "ArchiveUploadFailed"
    assert "Retry the task" in result["error"]["message"]
    keys = [o["Key"] for o in s3.list_objects_v2(Bucket=BUCKET)["Contents"]]
    assert keys == ["r2r/project-accounting-provisions/42/files/001-a.txt"]


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("report.pdf", "report.pdf"),
        ("../../etc/passwd", "_._etc_passwd"),
        ("Résumé (final).docx", "R_sum_ (final).docx"),
        ("...", "file"),
        ("a" * 200 + ".xlsx", "a" * 115 + ".xlsx"),
    ],
)
def test_safe_filename(filename: str, expected: str) -> None:
    assert safe_filename(filename) == expected
