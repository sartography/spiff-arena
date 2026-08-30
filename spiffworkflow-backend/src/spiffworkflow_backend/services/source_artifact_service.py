from __future__ import annotations

import hashlib
import json
import re
from typing import Any
from typing import TypedDict

SOURCE_ARTIFACT_CONTRACT_VERSION = "1.0"
SHA256_PATTERN = re.compile(r"^sha256-[a-f0-9]{64}$")


class SourceManifestFile(TypedDict):
    path: str
    revision: int
    content_type: str
    content_sha256: str


class SourceArtifactValidationError(ValueError):
    pass


def sha256(value: str) -> str:
    return f"sha256-{hashlib.sha256(value.encode('utf-8')).hexdigest()}"


def canonical_json(value: Any) -> str:
    return json.dumps(
        _canonical_value(value),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=False,
    )


def _canonical_value(value: Any) -> Any:
    if isinstance(value, dict):
        if not all(isinstance(key, str) for key in value):
            raise SourceArtifactValidationError("Canonical JSON object keys must be strings")
        return {
            key: _canonical_value(value[key])
            for key in sorted(value, key=lambda candidate: candidate.encode("utf-16be"))
        }
    if isinstance(value, list):
        return [_canonical_value(child) for child in value]
    if isinstance(value, float):
        raise SourceArtifactValidationError("Canonical JSON contracts support only finite integer numbers")
    if value is None or isinstance(value, str | int | bool):
        return value
    raise SourceArtifactValidationError(f"Canonical JSON does not support {type(value).__name__}")


def source_manifest_digest(files: list[dict[str, Any]]) -> str:
    canonical_files: list[SourceManifestFile] = []
    seen_paths = set()
    for file in files:
        path = file.get("path")
        revision = file.get("revision")
        content_type = file.get("content_type")
        content_sha256 = file.get("content_sha256")
        if not isinstance(path, str) or not path or path.startswith("/") or ".." in path.split("/"):
            raise SourceArtifactValidationError(f"Invalid source manifest path: {path}")
        if path in seen_paths:
            raise SourceArtifactValidationError(f"Duplicate source manifest path: {path}")
        if not isinstance(revision, int) or isinstance(revision, bool) or revision < 1:
            raise SourceArtifactValidationError(f"Invalid revision for {path}")
        if not isinstance(content_type, str) or not content_type:
            raise SourceArtifactValidationError(f"Missing content type for {path}")
        if not isinstance(content_sha256, str) or SHA256_PATTERN.fullmatch(content_sha256) is None:
            raise SourceArtifactValidationError(f"Invalid content digest for {path}")
        seen_paths.add(path)
        canonical_files.append(
            {
                "path": path,
                "revision": revision,
                "content_type": content_type,
                "content_sha256": content_sha256,
            }
        )

    # JavaScript compares strings by UTF-16 code units. Using UTF-16BE here keeps
    # the digest stable even when source paths contain non-BMP characters.
    canonical_files.sort(key=lambda file: file["path"].encode("utf-16be"))
    return sha256(canonical_json({"files": canonical_files}))


def validate_source_artifact_package(package: dict[str, Any]) -> dict[str, str] | None:
    raw_ref = package.get("source_artifact_ref")
    if raw_ref is None:
        return None
    if not isinstance(raw_ref, dict):
        raise SourceArtifactValidationError("source_artifact_ref must be an object")

    required = {
        "contract_version",
        "tenant_id",
        "provider",
        "project_id",
        "snapshot_id",
        "manifest_sha256",
    }
    allowed = required | {"entry_process_model_id"}
    if set(raw_ref) - allowed:
        raise SourceArtifactValidationError("source_artifact_ref contains unsupported fields")
    if required - set(raw_ref):
        raise SourceArtifactValidationError("source_artifact_ref is missing required fields")
    if any(not isinstance(raw_ref[key], str) or not raw_ref[key].strip() for key in required):
        raise SourceArtifactValidationError("source_artifact_ref fields must be non-empty strings")
    if raw_ref["contract_version"] != SOURCE_ARTIFACT_CONTRACT_VERSION:
        raise SourceArtifactValidationError("Unsupported source_artifact_ref contract version")
    if raw_ref["provider"] != "filestore":
        raise SourceArtifactValidationError("Unsupported source artifact provider")
    if SHA256_PATTERN.fullmatch(raw_ref["manifest_sha256"]) is None:
        raise SourceArtifactValidationError("Invalid source artifact manifest digest")
    entry_process_model_id = raw_ref.get("entry_process_model_id")
    if entry_process_model_id is not None and (
        not isinstance(entry_process_model_id, str) or not entry_process_model_id.strip()
    ):
        raise SourceArtifactValidationError("entry_process_model_id must be a non-empty string")

    for package_key, ref_key in (
        ("tenant_id", "tenant_id"),
        ("project_id", "project_id"),
        ("snapshot_id", "snapshot_id"),
    ):
        if package.get(package_key) != raw_ref[ref_key]:
            raise SourceArtifactValidationError(f"source_artifact_ref {ref_key} does not match package {package_key}")

    raw_files = package.get("files")
    if not isinstance(raw_files, list):
        raise SourceArtifactValidationError("Files package must include a files array")
    manifest_files = []
    for raw_file in raw_files:
        if not isinstance(raw_file, dict):
            raise SourceArtifactValidationError("Source artifact files must be objects")
        content = raw_file.get("content")
        content_sha256 = raw_file.get("content_sha256")
        if not isinstance(content, str) or not isinstance(content_sha256, str):
            raise SourceArtifactValidationError("Source artifact files must include string content and content_sha256")
        if sha256(content) != content_sha256:
            raise SourceArtifactValidationError(f"Content digest mismatch for {raw_file.get('path')}")
        manifest_files.append(
            {
                "path": raw_file.get("source_path"),
                "revision": raw_file.get("revision"),
                "content_type": raw_file.get("content_type"),
                "content_sha256": content_sha256,
            }
        )

    if source_manifest_digest(manifest_files) != raw_ref["manifest_sha256"]:
        raise SourceArtifactValidationError("Source artifact manifest digest does not match package files")

    return {str(key): str(value) for key, value in raw_ref.items()}
