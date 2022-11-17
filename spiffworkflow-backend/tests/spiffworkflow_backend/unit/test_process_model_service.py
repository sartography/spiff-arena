"""Test_process_model_service."""
from flask import Flask
from flask.testing import FlaskClient
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec

from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.process_model_service import ProcessModelService


class TestProcessModelService(BaseTest):
    """TestProcessModelService."""

    def test_can_update_specified_attributes(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_can_update_specified_attributes."""
        self.create_process_group(
            client, with_super_admin_user, "test_group", "test_group"
        )
        process_model = load_test_spec(
            "test_group/hello_world",
            bpmn_file_name="hello_world.bpmn",
            process_model_source_directory="hello_world",
        )
        assert process_model.display_name == "test_group/hello_world"

        primary_process_id = process_model.primary_process_id
        assert primary_process_id == "Process_HelloWorld"

        ProcessModelService().update_process_model(process_model, {"display_name": "new_name"})

        assert process_model.display_name == "new_name"
        assert process_model.primary_process_id == primary_process_id
