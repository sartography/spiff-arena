import pytest

from spiffworkflow_backend.models.task_instructions_for_end_user import TaskInstructionsForEndUserModel
from spiffworkflow_backend.services.catalog_localization_service import CatalogLocalizationError
from spiffworkflow_backend.services.catalog_localization_service import CatalogLocalizationService
from spiffworkflow_backend.services.jinja_service import JinjaService


def test_instruction_translation_is_applied_before_jinja_rendering() -> None:
    rendered = CatalogLocalizationService.render_instruction_before_jinja(
        "Welcome, {{ pilot_name }}.",
        {"pilot_name": "<Artemis>"},
        translated_template="Bienvenido, {{ pilot_name }}.",
    )

    assert rendered == "Bienvenido, &lt;Artemis&gt;."


def test_static_choice_titles_localize_without_changing_canonical_values() -> None:
    source_schema = {
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


def test_queued_instruction_can_be_rendered_later_from_preserved_context() -> None:
    queued_instruction = TaskInstructionsForEndUserModel(
        instruction="Welcome, Artemis.",
        instruction_template="Welcome, {{ mission_name }}.",
        task_data={"mission_name": "Artemis"},
    )

    assert JinjaService.render_queued_instruction(
        queued_instruction,
        translated_template="Bienvenida, {{ mission_name }}.",
    ) == "Bienvenida, Artemis."
