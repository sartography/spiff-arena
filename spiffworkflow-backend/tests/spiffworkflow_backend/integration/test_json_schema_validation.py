from unittest.mock import patch

from flask.app import Flask
from starlette.testclient import TestClient

from spiffworkflow_backend.models.user import UserModel
from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestJsonSchemaValidation(BaseTest):
    """Test JSON schema validation on task submission."""

    def test_json_schema_validation_success(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test that valid data passes validation when enabled."""
        with patch.dict(app.config, {"SPIFFWORKFLOW_BACKEND_VALIDATE_USER_TASK_DATA_AGAINST_SCHEMA": True}):
            process_group_id = "test_group"
            process_model_id = "simple_form"
            process_model = self.create_group_and_model_with_bpmn(
                client,
                with_super_admin_user,
                process_group_id=process_group_id,
                process_model_id=process_model_id,
            )

            # Create and run instance
            response = self.create_process_instance_from_process_model_id_with_api(
                client,
                process_model.id,
                headers=self.logged_in_headers(with_super_admin_user),
            )
            process_instance_id = response.json()["id"]
            client.post(
                f"/v1.0/process-instances/{self.modify_process_identifier_for_path_param(process_model.id)}/{process_instance_id}/run",
                headers=self.logged_in_headers(with_super_admin_user),
            )

            # Get task
            response = client.get(
                "/v1.0/tasks",
                headers=self.logged_in_headers(with_super_admin_user),
            )
            task = response.json()["results"][0]
            task_id = task["id"]

            # Submit valid data
            valid_data = {"name": "Test User", "department": "IT"}
            response = client.put(
                f"/v1.0/tasks/{process_instance_id}/{task_id}",
                headers=self.logged_in_headers(with_super_admin_user, additional_headers={"Content-Type": "application/json"}),
                json=valid_data,
            )
            assert response.status_code == 200

    def test_json_schema_validation_failure(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test that invalid data is rejected when validation is enabled."""
        with patch.dict(app.config, {"SPIFFWORKFLOW_BACKEND_VALIDATE_USER_TASK_DATA_AGAINST_SCHEMA": True}):
            process_group_id = "test_group"
            process_model_id = "simple_form"
            process_model = self.create_group_and_model_with_bpmn(
                client,
                with_super_admin_user,
                process_group_id=process_group_id,
                process_model_id=process_model_id,
            )

            # Create and run instance
            response = self.create_process_instance_from_process_model_id_with_api(
                client,
                process_model.id,
                headers=self.logged_in_headers(with_super_admin_user),
            )
            process_instance_id = response.json()["id"]
            client.post(
                f"/v1.0/process-instances/{self.modify_process_identifier_for_path_param(process_model.id)}/{process_instance_id}/run",
                headers=self.logged_in_headers(with_super_admin_user),
            )

            # Get task
            response = client.get(
                "/v1.0/tasks",
                headers=self.logged_in_headers(with_super_admin_user),
            )
            task = response.json()["results"][0]
            task_id = task["id"]

            # Submit invalid data - missing required name field
            invalid_data = {"department": "IT"}
            response = client.put(
                f"/v1.0/tasks/{process_instance_id}/{task_id}",
                headers=self.logged_in_headers(with_super_admin_user, additional_headers={"Content-Type": "application/json"}),
                json=invalid_data,
            )
            assert response.status_code == 400
            assert "task_data_validation_error" in response.json()["error_code"]
            assert "required" in response.json()["message"].lower()

    def test_json_schema_validation_disabled(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test that invalid data is accepted when validation is disabled."""
        with patch.dict(app.config, {"SPIFFWORKFLOW_BACKEND_VALIDATE_USER_TASK_DATA_AGAINST_SCHEMA": False}):
            process_group_id = "test_group"
            process_model_id = "simple_form"
            process_model = self.create_group_and_model_with_bpmn(
                client,
                with_super_admin_user,
                process_group_id=process_group_id,
                process_model_id=process_model_id,
            )

            # Create and run instance
            response = self.create_process_instance_from_process_model_id_with_api(
                client,
                process_model.id,
                headers=self.logged_in_headers(with_super_admin_user),
            )
            process_instance_id = response.json()["id"]
            client.post(
                f"/v1.0/process-instances/{self.modify_process_identifier_for_path_param(process_model.id)}/{process_instance_id}/run",
                headers=self.logged_in_headers(with_super_admin_user),
            )

            # Get task
            response = client.get(
                "/v1.0/tasks",
                headers=self.logged_in_headers(with_super_admin_user),
            )
            task = response.json()["results"][0]
            task_id = task["id"]

            # Submit invalid data - missing required field should still work
            invalid_data = {"department": "IT"}
            response = client.put(
                f"/v1.0/tasks/{process_instance_id}/{task_id}",
                headers=self.logged_in_headers(with_super_admin_user, additional_headers={"Content-Type": "application/json"}),
                json=invalid_data,
            )
            assert response.status_code == 200
