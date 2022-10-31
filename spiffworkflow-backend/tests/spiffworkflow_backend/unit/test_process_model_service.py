"""Test_process_model_service."""
from flask import Flask
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec

from spiffworkflow_backend.services.process_model_service import ProcessModelService


class TestProcessModelService(BaseTest):
    """TestProcessModelService."""

    def test_can_update_specified_attributes(
        self, app: Flask, with_db_and_bpmn_file_cleanup: None
    ) -> None:
        """Test_can_update_specified_attributes."""
        process_model = load_test_spec("hello_world")
        assert process_model.display_name == "hello_world"

        primary_process_id = process_model.primary_process_id
        assert primary_process_id == "Process_HelloWorld"

        ProcessModelService().update_spec(process_model, {"display_name": "new_name"})

        assert process_model.display_name == "new_name"
        assert process_model.primary_process_id == primary_process_id
