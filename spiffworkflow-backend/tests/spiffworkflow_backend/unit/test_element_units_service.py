import os
import pytest
import tempfile
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
def app_enabled(app_some_cache_dir: Flask) -> Flask:
    app_some_cache_dir.config["SPIFFWORKFLOW_BACKEND_FEATURE_ELEMENT_UNITS_ENABLED"] = True
    yield app_some_cache_dir

@pytest.fixture()
def example_specs_json_str(app: Flask) -> str:
    path = os.path.join(
            app.instance_path,
            "..",
            "..",
            "tests",
            "data",
        "specs-json",
        "no-tasks.json")
    with open(path) as f:
        yield f.read()

@pytest.fixture()
def tmp_cache_dir_name() -> str:
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname
        
class TestElementUnitsService(BaseTest):
    """Tests the ElementUnitsService."""

    def test_cache_dir_env_is_respected(
        self,
        app_some_cache_dir: Flask,
    ) -> None:
        assert ElementUnitsService._cache_dir() == "some_cache_dir"

    def test_feature_disabled_if_env_is_false(
        self,
        app_disabled: Flask,
    ) -> None:
        assert not ElementUnitsService._enabled()
        
    def test_feature_enabled_if_env_is_true(
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
        result = ElementUnitsService.cache_element_units("", "", "")
        assert result is None
        
    # TODO: ok to get for process when disabled
    # TODO: ok to get for element when disabled

    def test_can_write_to_cache(
            self,
            app_enabled: Flask,
            example_specs_json_str: str,
            tmp_cache_dir_name: str,
            ) -> None:
        result = ElementUnitsService.cache_element_units(tmp_cache_dir_name, "testing", example_specs_json_str)
        assert result is None

    # TODO: get for process when enabled
    # TODO: get for element when enabled
