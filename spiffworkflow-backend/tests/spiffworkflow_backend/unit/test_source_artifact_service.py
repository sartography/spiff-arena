import pytest

from spiffworkflow_backend.services.source_artifact_service import SourceArtifactValidationError
from spiffworkflow_backend.services.source_artifact_service import sha256
from spiffworkflow_backend.services.source_artifact_service import source_manifest_digest
from spiffworkflow_backend.services.source_artifact_service import validate_source_artifact_package


def test_source_manifest_digest_matches_the_cross_runtime_contract_vector() -> None:
    files = [
        {
            "path": "main/schema.json",
            "revision": 3,
            "content_type": "application/json",
            "content_sha256": f"sha256-{'b' * 64}",
        },
        {
            "path": "main/main.bpmn",
            "revision": 2,
            "content_type": "application/xml",
            "content_sha256": f"sha256-{'a' * 64}",
        },
    ]

    assert source_manifest_digest(files) == "sha256-64d09005728871107173d8716641663e0c337c6d524b3cf7bf705055655022cf"
    assert source_manifest_digest(list(reversed(files))) == source_manifest_digest(files)


def test_source_artifact_package_rejects_content_tampering() -> None:
    content = "trusted"
    manifest_files = [
        {
            "path": "main.bpmn",
            "revision": 1,
            "content_type": "application/xml",
            "content_sha256": sha256(content),
        }
    ]
    package = {
        "tenant_id": "tenant-1",
        "project_id": "project-1",
        "snapshot_id": "snapshot-1",
        "source_artifact_ref": {
            "contract_version": "1.0",
            "tenant_id": "tenant-1",
            "provider": "filestore",
            "project_id": "project-1",
            "snapshot_id": "snapshot-1",
            "manifest_sha256": source_manifest_digest(manifest_files),
        },
        "files": [
            {
                "path": "main.bpmn",
                "source_path": "main.bpmn",
                "revision": 1,
                "content_type": "application/xml",
                "content_sha256": sha256(content),
                "content": "tampered",
            }
        ],
    }

    with pytest.raises(SourceArtifactValidationError, match="Content digest mismatch"):
        validate_source_artifact_package(package)
