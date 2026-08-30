import pytest

from spiffworkflow_backend.services.locale_catalog_service import LocaleCatalogValidationError
from spiffworkflow_backend.services.locale_catalog_service import locale_catalog_digest
from spiffworkflow_backend.services.locale_catalog_service import validate_compatible_locale_catalog


def locale_catalog() -> dict:
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


def test_catalog_matches_an_exact_pinned_source_process_and_locale() -> None:
    catalog = locale_catalog()
    catalog["integrity"] = locale_catalog_digest(catalog)
    assert catalog["integrity"] == "sha256-4c94e27a6e3cb912eb230fa4f2725d5a858259569dfc0b9ef560ff85e1d63688"

    assert validate_compatible_locale_catalog(
        catalog,
        source_artifact_ref=catalog["source_artifact_ref"],
        process_model_identifier="artemis/mission",
        requested_locale="es",
    ) == catalog


def test_catalog_rejects_a_different_source_snapshot() -> None:
    catalog = locale_catalog()
    catalog["integrity"] = locale_catalog_digest(catalog)
    different_source = {**catalog["source_artifact_ref"], "snapshot_id": "snapshot-2"}

    with pytest.raises(LocaleCatalogValidationError, match="does not match the process instance"):
        validate_compatible_locale_catalog(
            catalog,
            source_artifact_ref=different_source,
            process_model_identifier="artemis/mission",
            requested_locale="es",
        )
