from unittest.mock import MagicMock, patch

import pytest
from flask import Flask
from starlette.testclient import TestClient

from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.routes.process_api_blueprint import _get_process_model
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestProcessModelMetadataBackfillIntegration(BaseTest):
    @patch("spiffworkflow_backend.routes.process_models_controller.trigger_metadata_backfill")
    def test_process_model_update_triggers_metadata_backfill(
        self,
        mock_trigger_metadata_backfill: MagicMock,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        # Create a test user
        user = self.create_user_with_permission("test_user")

        # Create a process group and model
        process_model = self.create_process_model_with_metadata()

        # Setup mock for trigger_metadata_backfill
        mock_trigger_metadata_backfill.return_value = {"status": "triggered", "task_id": "test-task-id"}

        # Update the process model with new metadata extraction paths
        modified_process_model_identifier = process_model.id.replace("/", ":")
        new_metadata_paths = [
            {"key": "awesome_var", "path": "outer.inner"},
            {"key": "invoice_number", "path": "invoice_number"},
            {"key": "new_key", "path": "new.path"},  # Add a new path
        ]

        # Update the process model via API
        response = client.put(
            f"/v1.0/process-models/{modified_process_model_identifier}",
            json={
                "metadata_extraction_paths": new_metadata_paths,
                "display_name": process_model.display_name,
                "description": process_model.description,
            },
            headers=self.logged_in_headers(user),
        )

        # Assert response is successful
        assert response.status_code == 200

        # Check that the trigger_metadata_backfill function was called
        mock_trigger_metadata_backfill.assert_called_once()

        # Check that the old and new models were passed to trigger_metadata_backfill
        args, _ = mock_trigger_metadata_backfill.call_args
        old_model, new_model = args

        # Check old model had the original metadata paths
        assert len(old_model.metadata_extraction_paths) == 2
        assert old_model.metadata_extraction_paths[0]["key"] == "awesome_var"
        assert old_model.metadata_extraction_paths[1]["key"] == "invoice_number"

        # Check new model has the updated metadata paths
        assert len(new_model.metadata_extraction_paths) == 3
        assert new_model.metadata_extraction_paths[0]["key"] == "awesome_var"
        assert new_model.metadata_extraction_paths[1]["key"] == "invoice_number"
        assert new_model.metadata_extraction_paths[2]["key"] == "new_key"

    @patch("spiffworkflow_backend.routes.process_models_controller.trigger_metadata_backfill")
    def test_process_model_update_without_metadata_changes_does_not_trigger_backfill(
        self,
        mock_trigger_metadata_backfill: MagicMock,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        # Create a test user
        user = self.create_user_with_permission("test_user")

        # Create a process group and model
        process_model = self.create_process_model_with_metadata()

        # Update only the display name of the process model
        modified_process_model_identifier = process_model.id.replace("/", ":")

        # Update the process model via API
        response = client.put(
            f"/v1.0/process-models/{modified_process_model_identifier}",
            json={
                "display_name": "Updated Display Name",
                "description": process_model.description,
            },
            headers=self.logged_in_headers(user),
        )

        # Assert response is successful
        assert response.status_code == 200

        # Check that the trigger_metadata_backfill function was NOT called
        mock_trigger_metadata_backfill.assert_not_called()

        # Verify the display name was updated
        updated_model = _get_process_model(process_model.id)
        assert updated_model.display_name == "Updated Display Name"

