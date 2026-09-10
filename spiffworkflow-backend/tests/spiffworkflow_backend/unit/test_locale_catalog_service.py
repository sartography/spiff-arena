from typing import Any

import pytest

from spiffworkflow_backend.services.locale_catalog_service import LocaleCatalogValidationError
from spiffworkflow_backend.services.locale_catalog_service import locale_catalog_digest
from spiffworkflow_backend.services.locale_catalog_service import validate_compatible_locale_catalog


def locale_catalog() -> dict[str, Any]:
    return {
        "contract_version": "1.0",
        "catalog_id": "catalog-es",
        "catalog_version": 1,
        "workspace_id": "workspace-1",
        "source_artifact_ref": {
            "contract_version": "1.0",
            "tenant_id": "tenant-1",
            "provider": "filestore",
            "project_id": "project-1",
            "snapshot_id": "snapshot-1",
            "manifest_sha256": f"sha256-{'a' * 64}",
        },
        "process_model_identifiers": ["artemis/mission"],
        "bpmn_version_control_identifier": "abc1234",
        "source_locale": "en",
        "target_locale": "es",
        "fallback_locale": "en",
        "published_at": "2026-08-30T12:00:00Z",
        "messages": {
            "bpmn:launch:instructions": {
                "value": "Bienvenido, {{ pilot_name }}.",
                "source_fingerprint": f"sha256-{'b' * 64}",
                "token_signature": ["{{ pilot_name }}"],
            }
        },
    }


def test_catalog_matches_the_existing_process_model_revision_linkage() -> None:
    catalog = locale_catalog()
    catalog["integrity"] = locale_catalog_digest(catalog)
    assert catalog["integrity"] == "sha256-4834da259608e538f90a6f2ebe72cd72efc70c8a2ca2bd27395369c6caec830b"

    assert (
        validate_compatible_locale_catalog(
            catalog,
            process_model_identifier="artemis/mission",
            bpmn_version_control_identifier="abc1234",
            requested_locale="es",
        )
        == catalog
    )


def test_catalog_rejects_a_different_process_model_revision() -> None:
    catalog = locale_catalog()
    catalog["integrity"] = locale_catalog_digest(catalog)

    with pytest.raises(LocaleCatalogValidationError, match="BPMN revision does not match"):
        validate_compatible_locale_catalog(
            catalog,
            process_model_identifier="artemis/mission",
            bpmn_version_control_identifier="def5678",
            requested_locale="es",
        )
