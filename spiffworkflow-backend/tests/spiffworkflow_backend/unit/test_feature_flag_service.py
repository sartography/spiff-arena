from collections.abc import Generator

import pytest
from flask.app import Flask
from spiffworkflow_backend.services.feature_flag_service import FeatureFlagService

from tests.spiffworkflow_backend.helpers.base_test import BaseTest


@pytest.fixture()
def no_feature_flags(app: Flask, with_db_and_bpmn_file_cleanup: None) -> Generator[None, None, None]:
    yield


class TestFeatureFlagService(BaseTest):
    """Tests the FeatureFlagService."""

    @pytest.mark.parametrize(
        "default_enabled,expected",
        [
            pytest.param(True, True),
            pytest.param(False, False),
        ],
    )
    def test_default_enabled_v0(
        self,
        no_feature_flags: None,
        default_enabled: bool,
        expected: bool,
    ) -> None:
        assert FeatureFlagService.feature_enabled("some_feature", default_enabled) == expected

    def test_default_feature_flag_value_overrides_passed_in_default_enabled(
        self,
        no_feature_flags: None,
    ) -> None:
        FeatureFlagService.set_feature_flags({"some_feature": False}, {})
        assert not FeatureFlagService.feature_enabled("some_feature", True)

    def test_process_model_override_feature_flag_value_overrides_passed_in_default_enabled(
        self,
        app: Flask,
        no_feature_flags: None,
    ) -> None:
        app.config.get("THREAD_LOCAL_DATA").process_model_identifier = "a/b/c"  # type: ignore
        FeatureFlagService.set_feature_flags(
            {},
            {"a/b/c": {"some_feature": False}},
        )
        assert not FeatureFlagService.feature_enabled("some_feature", True)

    def test_process_model_override_feature_flag_value_overrides_default_feature_flag_value(
        self,
        app: Flask,
        no_feature_flags: None,
    ) -> None:
        app.config.get("THREAD_LOCAL_DATA").process_model_identifier = "a/b/c"  # type: ignore
        FeatureFlagService.set_feature_flags(
            {"some_feature": True},
            {"a/b/c": {"some_feature": False}},
        )
        assert not FeatureFlagService.feature_enabled("some_feature", True)

    def test_does_not_consider_other_features(
        self,
        app: Flask,
        no_feature_flags: None,
    ) -> None:
        app.config.get("THREAD_LOCAL_DATA").process_model_identifier = "a/b/c"  # type: ignore
        FeatureFlagService.set_feature_flags(
            {"one_feature": False},
            {"a/b/c": {"two_feature": False}},
        )
        assert FeatureFlagService.feature_enabled("some_feature", True)
