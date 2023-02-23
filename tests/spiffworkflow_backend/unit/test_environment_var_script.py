"""Test_environment_var_script."""
from flask import Flask
from tests.spiffworkflow_backend.helpers.base_test import BaseTest

from spiffworkflow_backend.services.process_instance_processor import (
    ProcessInstanceProcessor,
)


class TestEnvironmentVarScript(BaseTest):
    """TestEnvironmentVarScript."""

    # it's not totally obvious we want to keep this test/file
    def test_script_engine_can_use_custom_scripts(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        """Test_script_engine_takes_data_and_returns_expected_results."""
        with app.app_context():
            script_engine = ProcessInstanceProcessor._script_engine
            result = script_engine._evaluate("get_env()", {})
            assert result == "unit_testing"
