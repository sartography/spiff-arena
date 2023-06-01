from flask import Flask
from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.get_env import GetEnv

from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestGetEnv(BaseTest):
    def test_get_env_script(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_model_identifier = "test_process_model"
        process_instance_id = 1
        script_attributes_context = ScriptAttributesContext(
            task=None,
            environment_identifier="unit_testing",
            process_instance_id=process_instance_id,
            process_model_identifier=process_model_identifier,
        )
        result = GetEnv().run(
            script_attributes_context,
        )
        assert result == "unit_testing"
