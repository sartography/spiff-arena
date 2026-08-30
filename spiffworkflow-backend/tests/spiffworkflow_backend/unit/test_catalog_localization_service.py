from typing import Any

import pytest

from spiffworkflow_backend.services.catalog_localization_service import CatalogLocalizationError
from spiffworkflow_backend.services.catalog_localization_service import CatalogLocalizationService


def test_instruction_translation_is_applied_before_jinja_rendering() -> None:
    rendered = CatalogLocalizationService.render_instruction_before_jinja(
        "Welcome, {{ pilot_name }}.",
        {"pilot_name": "<Artemis>"},
        translated_template="Bienvenido, {{ pilot_name }}.",
    )

    assert rendered == "Bienvenido, &lt;Artemis&gt;."


def test_static_choice_titles_localize_without_changing_canonical_values() -> None:
    source_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "destination": {
                "title": "Destination",
                "oneOf": [
                    {"const": "moon", "title": "Moon"},
                    {"const": "mars", "title": "Mars"},
                ],
            }
        },
    }

    localized_schema = CatalogLocalizationService.localize_json_presentation(
        source_schema,
        {
            "/properties/destination/title": "Destino",
            "/properties/destination/oneOf/0/title": "Luna",
            "/properties/destination/oneOf/1/title": "Marte",
        },
    )

    assert localized_schema["properties"]["destination"]["oneOf"] == [
        {"const": "moon", "title": "Luna"},
        {"const": "mars", "title": "Marte"},
    ]
    assert source_schema["properties"]["destination"]["oneOf"][0]["title"] == "Moon"


def test_schema_localization_rejects_canonical_value_targets() -> None:
    with pytest.raises(CatalogLocalizationError, match="not a presentation field"):
        CatalogLocalizationService.localize_json_presentation(
            {"oneOf": [{"const": "moon", "title": "Moon"}]},
            {"/oneOf/0/const": "luna"},
        )


@pytest.mark.parametrize("array_index", ["-1", "00", "01"])
def test_schema_localization_rejects_noncanonical_array_indexes(array_index: str) -> None:
    with pytest.raises(CatalogLocalizationError, match="Invalid translation pointer"):
        CatalogLocalizationService.localize_json_presentation(
            {"oneOf": [{"const": "moon", "title": "Moon"}]},
            {f"/oneOf/{array_index}/title": "Luna"},
        )
