import pytest
from flask.app import Flask
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from typing import Optional

from spiffworkflow_backend.services.element_units_service import (
    ElementUnitsService,
)

@pytest.fixture()
def app_no_cache_dir(app: Flask) -> Flask:
    app.config["SPIFFWORKFLOW_BACKEND_ELEMENT_UNITS_CACHE_DIR"] = None
    yield app

@pytest.fixture()
def app_some_cache_dir(app: Flask) -> Flask:
    app.config["SPIFFWORKFLOW_BACKEND_ELEMENT_UNITS_CACHE_DIR"] = "some_cache_dir"
    yield app

@pytest.fixture()
def app_disabled(app: Flask) -> Flask:
    app.config["SPIFFWORKFLOW_BACKEND_FEATURE_ELEMENT_UNITS_ENABLED"] = False
    yield app

@pytest.fixture()
def app_enabled(app: Flask) -> Flask:
    app.config["SPIFFWORKFLOW_BACKEND_ELEMENT_UNITS_CACHE_DIR"] = "some_cache_dir"
    app.config["SPIFFWORKFLOW_BACKEND_FEATURE_ELEMENT_UNITS_ENABLED"] = True
    yield app

class TestElementUnitsService(BaseTest):
    """Tests the ElementUnitsService."""

    def test_cache_dir_env_is_respected(
        self,
        app_some_cache_dir: Flask,
    ) -> None:
        assert ElementUnitsService._cache_dir() == "some_cache_dir"

    def test_feature_disabled_env_is_false(
        self,
        app_disabled: Flask,
    ) -> None:
        assert not ElementUnitsService._enabled()
        
    def test_feature_enabled_env_is_true(
        self,
        app_enabled: Flask,
    ) -> None:
        assert ElementUnitsService._enabled()

    def test_is_disabled_when_no_cache_dir(
        self,
        app_no_cache_dir: Flask,
    ) -> None:
        assert not ElementUnitsService._enabled()

    def test_ok_to_cache_when_disabled(
        self,
        app_disabled: Flask,
    ) -> None:
        result = ElementUnitsService.cache_element_units()
        assert result is None
