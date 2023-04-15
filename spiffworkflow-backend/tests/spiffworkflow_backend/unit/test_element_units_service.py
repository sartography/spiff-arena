from flask.app import Flask
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from typing import Optional

from spiffworkflow_backend.services.element_units_service import (
    ElementUnitsService,
)

class ElementUnitsServiceWithNoCacheDir(ElementUnitsService):
    """Fake."""
    @classmethod
    def _cache_dir(cls) -> Optional[str]:
        return None

class ElementUnitsServiceThatIsNotEnabled(ElementUnitsService):
    """Fake."""
    @classmethod
    def _enabled(cls) -> bool:
        return False

class TestElementUnitsService(BaseTest):
    """Tests the ElementUnitsService."""

    def test_ok_to_cache_with_no_cache_dir(
        self,
        app: Flask,
    ) -> None:
        result = ElementUnitsServiceWithNoCacheDir.cache_element_units()
        assert result is None

    def test_ok_to_cache_when_disabled(
        self,
        app: Flask,
    ) -> None:
        result = ElementUnitsServiceThatIsNotEnabled.cache_element_units()
        assert result is None
