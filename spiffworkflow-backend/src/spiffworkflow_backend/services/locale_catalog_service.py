from __future__ import annotations

import hashlib
import json
import re
from typing import Any

SHA256_PATTERN = re.compile(r"^sha256-[a-f0-9]{64}$")


class LocaleCatalogValidationError(ValueError):
    pass


def locale_catalog_digest(catalog: dict[str, Any]) -> str:
    unsigned_catalog = {key: value for key, value in catalog.items() if key != "integrity"}
    digest = hashlib.sha256(_canonical_json(unsigned_catalog).encode("utf-8")).hexdigest()
    return f"sha256-{digest}"


def validate_compatible_locale_catalog(
    catalog: dict[str, Any],
    *,
    process_model_identifier: str,
    bpmn_version_control_identifier: str,
    requested_locale: str,
) -> dict[str, Any]:
    required = {
        "contract_version",
        "catalog_id",
        "catalog_version",
        "workspace_id",
        "source_artifact_ref",
        "process_model_identifiers",
        "bpmn_version_control_identifier",
        "source_locale",
        "target_locale",
        "fallback_locale",
        "published_at",
        "messages",
        "integrity",
    }
    allowed = required | {"published_by", "validation_summary", "provenance"}
    if set(catalog) - allowed:
        raise LocaleCatalogValidationError("Locale catalog contains unsupported fields")
    if required - set(catalog):
        raise LocaleCatalogValidationError("Locale catalog is missing required fields")
    if catalog.get("contract_version") != "1.0":
        raise LocaleCatalogValidationError("Unsupported locale catalog contract version")
    for key in (
        "catalog_id",
        "workspace_id",
        "bpmn_version_control_identifier",
        "source_locale",
        "target_locale",
        "fallback_locale",
        "published_at",
    ):
        if not isinstance(catalog.get(key), str) or not catalog[key]:
            raise LocaleCatalogValidationError(f"Locale catalog {key} must be a non-empty string")
    if not isinstance(catalog.get("source_artifact_ref"), dict):
        raise LocaleCatalogValidationError("Locale catalog source_artifact_ref must be an object")
    if not isinstance(catalog.get("catalog_version"), int) or isinstance(catalog["catalog_version"], bool):
        raise LocaleCatalogValidationError("Locale catalog version must be an integer")
    if catalog["catalog_version"] < 1:
        raise LocaleCatalogValidationError("Locale catalog version must be positive")
    if "published_by" in catalog and (not isinstance(catalog["published_by"], str) or not catalog["published_by"]):
        raise LocaleCatalogValidationError("Locale catalog published_by must be a non-empty string")
    for metadata_key in ("validation_summary", "provenance"):
        if metadata_key in catalog and not isinstance(catalog[metadata_key], dict):
            raise LocaleCatalogValidationError(f"Locale catalog {metadata_key} must be an object")
    if catalog["bpmn_version_control_identifier"] != bpmn_version_control_identifier:
        raise LocaleCatalogValidationError("Locale catalog BPMN revision does not match the process instance")
    if catalog["target_locale"] != requested_locale:
        raise LocaleCatalogValidationError("Locale catalog target locale does not match the requested locale")

    process_model_identifiers = catalog.get("process_model_identifiers")
    if (
        not isinstance(process_model_identifiers, list)
        or not process_model_identifiers
        or not all(isinstance(identifier, str) and identifier for identifier in process_model_identifiers)
        or len(set(process_model_identifiers)) != len(process_model_identifiers)
    ):
        raise LocaleCatalogValidationError("Locale catalog process_model_identifiers must be unique non-empty strings")
    if process_model_identifier not in process_model_identifiers:
        raise LocaleCatalogValidationError("Locale catalog does not include the requested process model")

    messages = catalog.get("messages")
    if not isinstance(messages, dict) or not messages:
        raise LocaleCatalogValidationError("Locale catalog must contain at least one message")
    for content_unit_id, message in messages.items():
        if not isinstance(content_unit_id, str) or not content_unit_id or not isinstance(message, dict):
            raise LocaleCatalogValidationError("Locale catalog messages are invalid")
        if set(message) != {"value", "source_fingerprint", "token_signature"}:
            raise LocaleCatalogValidationError(f"Locale catalog message {content_unit_id} has unsupported fields")
        if not isinstance(message.get("value"), str):
            raise LocaleCatalogValidationError(f"Locale catalog message {content_unit_id} has an invalid value")
        if (
            not isinstance(message.get("source_fingerprint"), str)
            or SHA256_PATTERN.fullmatch(message["source_fingerprint"]) is None
        ):
            raise LocaleCatalogValidationError(f"Locale catalog message {content_unit_id} has an invalid source fingerprint")
        if not isinstance(message.get("token_signature"), list) or not all(
            isinstance(token, str) for token in message["token_signature"]
        ):
            raise LocaleCatalogValidationError(f"Locale catalog message {content_unit_id} has an invalid token signature")

    integrity = catalog.get("integrity")
    if not isinstance(integrity, str) or SHA256_PATTERN.fullmatch(integrity) is None:
        raise LocaleCatalogValidationError("Locale catalog integrity digest is invalid")
    if locale_catalog_digest(catalog) != integrity:
        raise LocaleCatalogValidationError("Locale catalog integrity digest does not match its content")
    return catalog


def _canonical_json(value: Any) -> str:
    return json.dumps(
        _canonical_value(value),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=False,
    )


def _canonical_value(value: Any) -> Any:
    if isinstance(value, dict):
        if not all(isinstance(key, str) for key in value):
            raise LocaleCatalogValidationError("Canonical JSON object keys must be strings")
        return {key: _canonical_value(value[key]) for key in sorted(value, key=lambda candidate: candidate.encode("utf-16be"))}
    if isinstance(value, list):
        return [_canonical_value(child) for child in value]
    if isinstance(value, float):
        raise LocaleCatalogValidationError("Canonical JSON contracts support only finite integer numbers")
    if value is None or isinstance(value, str | int | bool):
        return value
    raise LocaleCatalogValidationError(f"Canonical JSON does not support {type(value).__name__}")
