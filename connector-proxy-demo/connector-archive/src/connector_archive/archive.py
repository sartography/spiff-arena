"""Builds the archive for one process run: the summary PDF, the uploaded files, and a manifest.

Storage is kept apart from the archive layout, so a destination such as SharePoint can reuse
build_archive_entries and only add its own upload step.
"""

import base64
import binascii
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import UTC
from datetime import datetime
from typing import Any
from urllib.parse import unquote

from connector_archive.report_pdf import render_report_pdf

SUMMARY_FILENAME = "summary.pdf"
MANIFEST_FILENAME = "manifest.json"
MAX_FILENAME_LENGTH = 120


class ArchiveInputError(ValueError):
    pass


@dataclass
class ArchiveEntry:
    key: str
    body: bytes
    content_type: str
    sha256: str
    original_filename: str | None = None
    uploaded_at: str | None = None

    @property
    def size(self) -> int:
        return len(self.body)


def safe_filename(filename: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._()\- ]+", "_", filename).strip(" .")
    cleaned = re.sub(r"_+", "_", re.sub(r"\.{2,}", ".", cleaned))
    if len(cleaned) > MAX_FILENAME_LENGTH:
        stem, dot, extension = cleaned.rpartition(".")
        if dot and len(extension) <= 10:
            cleaned = stem[: MAX_FILENAME_LENGTH - len(extension) - 1] + "." + extension
        else:
            cleaned = cleaned[:MAX_FILENAME_LENGTH]
    return cleaned or "file"


def normalize_key_prefix(key_prefix: str) -> str:
    parts = [part for part in key_prefix.split("/") if part]
    if not parts or any(part in (".", "..") for part in parts):
        raise ArchiveInputError("key_prefix must be a path like 'group/model/123' without '.' or '..' parts.")
    return "/".join(parts)


def parse_data_url(data_url: str) -> tuple[str, str, bytes]:
    """Return (mimetype, filename, contents) for 'data:<mimetype>;name=<filename>;base64,<data>'."""
    if not isinstance(data_url, str) or not data_url.startswith("data:") or ";base64," not in data_url:
        raise ArchiveInputError("Each file must be a base64 data url. Use get_process_instance_files(include_contents=True).")
    metadata, encoded_contents = data_url[len("data:") :].rsplit(";base64,", 1)
    if encoded_contents.startswith("spifffiledatadigest+"):
        raise ArchiveInputError(
            "A file was passed as a digest reference, not its contents. "
            "Use get_process_instance_files(include_contents=True) or get_encoded_file_data()."
        )
    mimetype, _, encoded_filename = metadata.partition(";name=")
    try:
        contents = base64.b64decode(encoded_contents, validate=True)
    except binascii.Error as exception:
        raise ArchiveInputError(f"A file has invalid base64 contents: {exception}") from exception
    return (mimetype or "application/octet-stream", unquote(encoded_filename) or "file", contents)


def _uploaded_at_text(file_input: dict) -> str | None:
    created_at = file_input.get("created_at_in_seconds")
    if isinstance(created_at, int | float):
        return datetime.fromtimestamp(created_at, UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    uploaded_at = file_input.get("uploaded_at")
    return str(uploaded_at) if uploaded_at else None


def _file_entries(files: list, key_prefix: str) -> list[ArchiveEntry]:
    entries = []
    for index, file_input in enumerate(files, start=1):
        if isinstance(file_input, str):
            file_input = {"data_url": file_input}
        if not isinstance(file_input, dict) or "data_url" not in file_input:
            raise ArchiveInputError("Each file must be a data url string or a dict with a data_url key.")
        mimetype, filename_from_url, contents = parse_data_url(file_input["data_url"])
        filename = str(file_input.get("filename") or filename_from_url)
        sha256 = hashlib.sha256(contents).hexdigest()
        expected_digest = file_input.get("digest")
        if expected_digest and expected_digest != sha256:
            raise ArchiveInputError(f"File {index} ({filename}) does not match its stored digest.")
        entries.append(
            ArchiveEntry(
                key=f"{key_prefix}/files/{index:03d}-{safe_filename(filename)}",
                body=contents,
                content_type=str(file_input.get("mimetype") or mimetype),
                sha256=sha256,
                original_filename=filename,
                uploaded_at=_uploaded_at_text(file_input),
            )
        )
    return entries


def build_archive_entries(
    report: dict,
    files: list | None,
    key_prefix: str,
    generated_at: datetime | None = None,
) -> list[ArchiveEntry]:
    """Return the entries in upload order: the files, then the summary PDF, then the manifest.

    The manifest is last so its presence means the archive is complete.
    """
    if files is None:
        files = []
    if not isinstance(files, list):
        raise ArchiveInputError("files must be a list.")
    key_prefix = normalize_key_prefix(key_prefix)
    generated_at = generated_at or datetime.now(UTC)

    file_entries = _file_entries(files, key_prefix)
    archived_files = [
        {
            "archive_key": entry.key,
            "original_filename": entry.original_filename,
            "mimetype": entry.content_type,
            "size": entry.size,
            "sha256": entry.sha256,
            "uploaded_at": entry.uploaded_at,
        }
        for entry in file_entries
    ]
    summary_pdf = render_report_pdf(report, archived_files, generated_at=generated_at)
    summary_entry = ArchiveEntry(
        key=f"{key_prefix}/{SUMMARY_FILENAME}",
        body=summary_pdf,
        content_type="application/pdf",
        sha256=hashlib.sha256(summary_pdf).hexdigest(),
    )
    manifest: dict[str, Any] = {
        "manifest_version": 1,
        "title": report.get("title"),
        "generated_at": generated_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "key_prefix": key_prefix,
        "summary": {"key": summary_entry.key, "size": summary_entry.size, "sha256": summary_entry.sha256},
        "files": archived_files,
    }
    manifest_body = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8")
    manifest_entry = ArchiveEntry(
        key=f"{key_prefix}/{MANIFEST_FILENAME}",
        body=manifest_body,
        content_type="application/json",
        sha256=hashlib.sha256(manifest_body).hexdigest(),
    )
    return [*file_entries, summary_entry, manifest_entry]
