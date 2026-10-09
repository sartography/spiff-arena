from __future__ import annotations

import copy
import re
from typing import Any

from spiffworkflow_backend.services.jinja_service import JinjaService

ARRAY_INDEX_PATTERN = re.compile(r"0|[1-9][0-9]*")


class CatalogLocalizationError(ValueError):
    pass


class CatalogLocalizationService:
    PRESENTATION_KEYS = {"description", "title", "ui:description", "ui:title"}

    @classmethod
    def render_instruction_before_jinja(
        cls,
        source_template: str,
        task_data: dict[str, Any],
        translated_template: str | None = None,
    ) -> str:
        template = translated_template if translated_template is not None else source_template
        return JinjaService.render_jinja_template(template, task_data=task_data)

    @classmethod
    def localize_json_presentation(
        cls,
        source_document: dict[str, Any],
        translations_by_json_pointer: dict[str, str],
    ) -> dict[str, Any]:
        localized_document = copy.deepcopy(source_document)
        for pointer, translated_value in translations_by_json_pointer.items():
            cls._replace_presentation_value(localized_document, pointer, translated_value)
        return localized_document

    @classmethod
    def _replace_presentation_value(cls, document: dict[str, Any], pointer: str, translated_value: str) -> None:
        if not isinstance(translated_value, str):
            raise CatalogLocalizationError(f"Translation for {pointer} must be a string")
        segments = cls._json_pointer_segments(pointer)
        if not segments or segments[-1] not in cls.PRESENTATION_KEYS:
            raise CatalogLocalizationError(f"Translation target is not a presentation field: {pointer}")

        parent: Any = document
        for segment in segments[:-1]:
            if isinstance(parent, list):
                if ARRAY_INDEX_PATTERN.fullmatch(segment) is None:
                    raise CatalogLocalizationError(f"Invalid translation pointer: {pointer}")
                try:
                    parent = parent[int(segment)]
                except IndexError as exception:
                    raise CatalogLocalizationError(f"Invalid translation pointer: {pointer}") from exception
            elif isinstance(parent, dict) and segment in parent:
                parent = parent[segment]
            else:
                raise CatalogLocalizationError(f"Invalid translation pointer: {pointer}")

        leaf = segments[-1]
        if not isinstance(parent, dict) or leaf not in parent or not isinstance(parent[leaf], str):
            raise CatalogLocalizationError(f"Translation pointer does not identify a source string: {pointer}")
        parent[leaf] = translated_value

    @staticmethod
    def _json_pointer_segments(pointer: str) -> list[str]:
        if pointer == "":
            return []
        if not pointer.startswith("/"):
            raise CatalogLocalizationError(f"Invalid JSON Pointer: {pointer}")
        return [segment.replace("~1", "/").replace("~0", "~") for segment in pointer[1:].split("/")]
