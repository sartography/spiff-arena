from flask import Flask
from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.get_task_data_value import GetTaskDataValue

from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestGetTaskDataValue(BaseTest):
    def test_get_task_data_value_script(
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
        result = GetTaskDataValue().run(script_attributes_context, "the_var_name", "the_default_value")
        assert result == "the_default_value"
