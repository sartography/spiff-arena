"""Test_various_bpmn_constructs."""
import pytest
from flask.app import Flask
from flask_bpmn.api.api_error import ApiError
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec

from spiffworkflow_backend.services.process_instance_processor import (
    ProcessInstanceProcessor,
)


class TestOpenFile(BaseTest):
    """TestVariousBpmnConstructs."""

    def test_dot_notation(
        self, app: Flask, with_db_and_bpmn_file_cleanup: None
    ) -> None:
        """Test_form_data_conversion_to_dot_dict."""
        process_model = load_test_spec(
            "dangerous",
            bpmn_file_name="read_etc_passwd.bpmn",
            process_model_source_directory="dangerous-scripts",
        )
        self.find_or_create_user()

        process_instance = self.create_process_instance_from_process_model(
            process_model
        )
        processor = ProcessInstanceProcessor(process_instance)

        with pytest.raises(ApiError) as exception:
            processor.do_engine_steps(save=True)
        assert "name 'open' is not defined" in str(exception.value)


class TestImportModule(BaseTest):
    """TestVariousBpmnConstructs."""

    def test_dot_notation(
        self, app: Flask, with_db_and_bpmn_file_cleanup: None
    ) -> None:
        """Test_form_data_conversion_to_dot_dict."""
        process_model = load_test_spec(
            "dangerous",
            bpmn_file_name="read_env.bpmn",
            process_model_source_directory="dangerous-scripts",
        )
        self.find_or_create_user()

        process_instance = self.create_process_instance_from_process_model(
            process_model
        )
        processor = ProcessInstanceProcessor(process_instance)

        with pytest.raises(ApiError) as exception:
            processor.do_engine_steps(save=True)
        assert "Import not allowed: os" in str(exception.value)
