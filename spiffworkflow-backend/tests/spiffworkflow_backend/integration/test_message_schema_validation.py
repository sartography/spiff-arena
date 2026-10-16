import uuid

from flask import Flask
from starlette.testclient import TestClient

from spiffworkflow_backend.models.user import UserModel
from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestMessageSchemaValidation(BaseTest):
    """Test JSON schema validation on message sending."""

    def test_message_schema_validation_success(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test that valid message payload passes validation when enabled."""
        with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_VALIDATE_MESSAGE_BODY_AGAINST_SCHEMA", True):
            process_group_id = "test_group"
            process_model_id = "simple_form"
            self.create_group_and_model_with_bpmn(
                client,
                with_super_admin_user,
                process_group_id=process_group_id,
                process_model_id=process_model_id,
            )

            # Update process group with message definition containing a JSON schema
            response = client.put(
                f"/v1.0/process-groups/{process_group_id}",
                headers=self.logged_in_headers(with_super_admin_user, additional_headers={"Content-Type": "application/json"}),
                json={
                    "display_name": "Test Group",
                    "messages": {
                        "test_message": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "amount": {"type": "integer"}
                                },
                                "required": ["amount"],
                            }
                        }
                    },
                },
            )
            assert response.status_code == 200

            # Send valid message payload with TTL and UUID so it can be buffered if no listener is waiting
            valid_payload = {"amount": 100}
            modified_message_name = f"{process_group_id}:test_message"
            msg_uuid = str(uuid.uuid4())
            response = client.post(
                f"/v1.0/messages/{modified_message_name}?time_to_live_in_seconds=60&message_instance_uuid={msg_uuid}",
                headers=self.logged_in_headers(with_super_admin_user),
                json=valid_payload,
            )
            assert response.status_code in (200, 202)

    def test_message_schema_validation_failure(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test that invalid message payload is rejected when validation is enabled."""
        with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_VALIDATE_MESSAGE_BODY_AGAINST_SCHEMA", True):
            process_group_id = "test_group"
            process_model_id = "simple_form"
            self.create_group_and_model_with_bpmn(
                client,
                with_super_admin_user,
                process_group_id=process_group_id,
                process_model_id=process_model_id,
            )

            # Update process group with message definition containing a JSON schema
            response = client.put(
                f"/v1.0/process-groups/{process_group_id}",
                headers=self.logged_in_headers(with_super_admin_user, additional_headers={"Content-Type": "application/json"}),
                json={
                    "display_name": "Test Group",
                    "messages": {
                        "test_message": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "amount": {"type": "integer"}
                                },
                                "required": ["amount"],
                            }
                        }
                    },
                },
            )
            assert response.status_code == 200

            # Send invalid payload (missing required 'amount')
            invalid_payload = {"note": "missing amount"}
            modified_message_name = f"{process_group_id}:test_message"
            msg_uuid = str(uuid.uuid4())
            response = client.post(
                f"/v1.0/messages/{modified_message_name}?time_to_live_in_seconds=60&message_instance_uuid={msg_uuid}",
                headers=self.logged_in_headers(with_super_admin_user),
                json=invalid_payload,
            )
            assert response.status_code == 400
            assert response.json()["error_code"] == "message_data_validation_error"
            assert "required" in response.json()["message"].lower()
            assert "amount" in response.json()["message"].lower()

    def test_message_schema_validation_disabled(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test that invalid message payload is accepted when validation is disabled."""
        with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_VALIDATE_MESSAGE_BODY_AGAINST_SCHEMA", False):
            process_group_id = "test_group"
            process_model_id = "simple_form"
            self.create_group_and_model_with_bpmn(
                client,
                with_super_admin_user,
                process_group_id=process_group_id,
                process_model_id=process_model_id,
            )

            # Update process group with message definition containing a JSON schema
            response = client.put(
                f"/v1.0/process-groups/{process_group_id}",
                headers=self.logged_in_headers(with_super_admin_user, additional_headers={"Content-Type": "application/json"}),
                json={
                    "display_name": "Test Group",
                    "messages": {
                        "test_message": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "amount": {"type": "integer"}
                                },
                                "required": ["amount"],
                            }
                        }
                    },
                },
            )
            assert response.status_code == 200

            # Send invalid payload - should be accepted because validation is disabled
            invalid_payload = {"note": "missing amount"}
            modified_message_name = f"{process_group_id}:test_message"
            msg_uuid = str(uuid.uuid4())
            response = client.post(
                f"/v1.0/messages/{modified_message_name}?time_to_live_in_seconds=60&message_instance_uuid={msg_uuid}",
                headers=self.logged_in_headers(with_super_admin_user),
                json=invalid_payload,
            )
            assert response.status_code in (200, 202)
