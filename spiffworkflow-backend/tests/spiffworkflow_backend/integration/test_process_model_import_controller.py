"""Tests for the process model import functionality.

Note: These tests expect the backend service to be restarted after making changes
to the API definitions. The tests will fail with 500 errors until the backend is
restarted with the new API definitions.
"""

import json
import os
from unittest.mock import patch

from flask.app import Flask
from starlette.testclient import TestClient

from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.process_model_import_service import ProcessModelImportService
from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestProcessModelImportController(BaseTest):
    def test_process_model_import_from_github(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test importing a process model from a GitHub URL."""
        process_group_id = "test_group"

        # Create a process group first
        self.create_process_group_with_api(
            client=client, user=with_super_admin_user, process_group_id=process_group_id, display_name="Test Group"
        )

        # Mock the ProcessModelImportService.import_from_github_url method
        mock_process_model = ProcessModelInfo(
            id=f"{process_group_id}/imported_model",
            display_name="Imported Model",
            description="Imported from GitHub",
            primary_process_id="imported_process",
            primary_file_name="imported_model.bpmn",
        )

        with patch.object(ProcessModelImportService, "import_from_github_url", return_value=mock_process_model) as mock_import:
            # Make a request to the import endpoint
            repository_url = "https://github.com/sartography/example-process-models/tree/main/examples/0-1-minimal-example"
            response = client.post(
                f"/v1.0/process-model-import/{process_group_id}",
                json={"repository_url": repository_url},
                headers=self.logged_in_headers(with_super_admin_user),
            )

            # Check the response status code
            assert response.status_code == 201

            # Verify the response data
            response_data = json.loads(response.content)
            assert "process_model" in response_data
            assert response_data["process_model"]["id"] == f"{process_group_id}/imported_model"
            assert response_data["process_model"]["display_name"] == "Imported Model"
            assert response_data["process_model"]["description"] == "Imported from GitHub"
            assert response_data["import_source"] == repository_url

            # Verify the service method was called correctly
            mock_import.assert_called_once_with(url=repository_url, process_group_id=process_group_id)

    def test_process_model_import_missing_url(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test importing a process model with a missing URL."""
        process_group_id = "test_group"

        # Create a process group first
        self.create_process_group_with_api(
            client=client, user=with_super_admin_user, process_group_id=process_group_id, display_name="Test Group"
        )

        # Make a request to the import endpoint without a repository_url
        response = client.post(
            f"/v1.0/process-model-import/{process_group_id}",
            json={},
            headers=self.logged_in_headers(with_super_admin_user),
        )

        # Fix the URL to use the correct API endpoint
        # Check the response status code
        assert response.status_code == 400

        # Verify the error message
        response_data = json.loads(response.content)
        assert response_data["title"] == "Bad Request"
        assert "'repository_url' is a required property" in response_data["detail"]

    def test_process_model_import_invalid_group(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test importing a process model to a non-existent group."""
        process_group_id = "nonexistent_group"

        repository_url = "https://github.com/sartography/example-process-models/tree/main/examples/0-1-minimal-example"
        response = client.post(
            f"/v1.0/process-model-import/{process_group_id}",
            json={"repository_url": repository_url},
            headers=self.logged_in_headers(with_super_admin_user),
        )

        # Check the response status code
        assert response.status_code == 500

        # Verify the error message
        response_data = json.loads(response.content)
        assert "error_code" in response_data
        assert response_data["error_code"] == "internal_server_error"
        assert "process_group_not_found" in response_data["message"]
        
    def test_process_model_import_from_model_alias(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test importing a process model from a marketplace model alias."""
        process_group_id = "test_group"

        # Create a process group first
        self.create_process_group_with_api(
            client=client, user=with_super_admin_user, process_group_id=process_group_id, display_name="Test Group"
        )

        # Mock the ProcessModelImportService.import_from_model_alias method
        mock_process_model = ProcessModelInfo(
            id=f"{process_group_id}/timer_events",
            display_name="Timer Events",
            description="Imported from marketplace: timer-events",
            primary_process_id="timer_events_process",
            primary_file_name="timer-events.bpmn",
        )

        with patch.object(ProcessModelImportService, "is_model_alias", return_value=True), \
             patch.object(ProcessModelImportService, "import_from_model_alias", return_value=mock_process_model) as mock_import:
            # Make a request to the import endpoint with a model alias
            model_alias = "timer-events"
            response = client.post(
                f"/v1.0/process-model-import/{process_group_id}",
                json={"repository_url": model_alias},
                headers=self.logged_in_headers(with_super_admin_user),
            )

            # Check the response status code
            assert response.status_code == 201

            # Verify the response data
            response_data = json.loads(response.content)
            assert "process_model" in response_data
            assert response_data["process_model"]["id"] == f"{process_group_id}/timer_events"
            assert response_data["process_model"]["display_name"] == "Timer Events"
            assert response_data["process_model"]["description"] == "Imported from marketplace: timer-events"
            assert response_data["import_source"] == model_alias

            # Verify the service method was called correctly
            mock_import.assert_called_once_with(alias=model_alias, process_group_id=process_group_id)
            
    def test_is_model_alias(self) -> None:
        """Test the is_model_alias method."""
        # Valid model aliases
        assert ProcessModelImportService.is_model_alias("timer-events") is True
        assert ProcessModelImportService.is_model_alias("simple_example") is True
        assert ProcessModelImportService.is_model_alias("example123") is True
        
        # Invalid model aliases
        assert ProcessModelImportService.is_model_alias("https://github.com/example") is False
        assert ProcessModelImportService.is_model_alias("example with spaces") is False
        assert ProcessModelImportService.is_model_alias("example/with/slashes") is False
        
    def test_get_marketplace_url(self) -> None:
        """Test the get_marketplace_url method."""
        # Save the original environment variable value
        original_url = os.environ.get("SPIFFWORKFLOW_BACKEND_MODEL_MARKETPLACE_URL")
        
        try:
            # Set a custom URL
            os.environ["SPIFFWORKFLOW_BACKEND_MODEL_MARKETPLACE_URL"] = "https://custom-marketplace.example.com"
            assert ProcessModelImportService.get_marketplace_url() == "https://custom-marketplace.example.com"
            
            # Remove the environment variable to test the default value
            if "SPIFFWORKFLOW_BACKEND_MODEL_MARKETPLACE_URL" in os.environ:
                del os.environ["SPIFFWORKFLOW_BACKEND_MODEL_MARKETPLACE_URL"]
            assert ProcessModelImportService.get_marketplace_url() == "http://127.0.0.1:8000"
        finally:
            # Restore the original value
            if original_url is not None:
                os.environ["SPIFFWORKFLOW_BACKEND_MODEL_MARKETPLACE_URL"] = original_url
            elif "SPIFFWORKFLOW_BACKEND_MODEL_MARKETPLACE_URL" in os.environ:
                del os.environ["SPIFFWORKFLOW_BACKEND_MODEL_MARKETPLACE_URL"]
