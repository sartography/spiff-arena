from flask import Flask
from starlette.testclient import TestClient

from spiffworkflow_backend.models.api_log_model import APILogModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.user import UserModel
from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestAPILogging(BaseTest):
    def test_message_send_logging(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test that sending a message creates a log entry."""
        with app.app_context():
            # Clear existing logs
            db.session.query(APILogModel).delete()
            db.session.commit()

            # Enable API logging for this test
            with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_API_LOGGING_ENABLED", True):
                # URL: /v1.0/messages/<modified_message_name>
                # We use a message name that might not exist, but we expect the logging to happen anyway
                # or at least we expect the controller to be called.
                # If the controller returns 404, the logging decorator should still run if it wraps the controller.
                # Wait, if the controller returns 404 because the message definition is not found,
                # the controller IS called (it's inside message_send that it looks up the message).

                response = client.post(
                    "/v1.0/messages/test_message",
                    json={"payload": {"key": "value"}},
                    headers=self.logged_in_headers(
                        with_super_admin_user, additional_headers={"Content-Type": "application/json"}
                    ),
                )

                # Even if it fails (404/500), it should log
                logs = db.session.query(APILogModel).all()
                assert len(logs) == 1
                log = logs[0]
                assert log.endpoint == "/v1.0/messages/test_message"
                assert log.method == "POST"
                assert log.request_body == {"payload": {"key": "value"}}
                assert log.status_code == response.status_code

    def test_process_instance_run_logging(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test that running a process instance creates a log entry."""
        with app.app_context():
            # Clear existing logs
            db.session.query(APILogModel).delete()
            db.session.commit()

            # Enable API logging for this test
            with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_API_LOGGING_ENABLED", True):
                # URL: /v1.0/process-instance-run/<process_model_id>/<process_instance_id>
                client.post(
                    "/v1.0/process-instance-run/test_model/123",
                    json={},
                    headers=self.logged_in_headers(
                        with_super_admin_user, additional_headers={"Content-Type": "application/json"}
                    ),
                )

                logs = db.session.query(APILogModel).all()
                assert len(logs) == 1
                log = logs[0]
                assert log.endpoint == "/v1.0/process-instance-run/test_model/123"
                assert log.method == "POST"
                assert log.process_instance_id == 123  # Should be extracted from URL/kwargs if not in response

    def test_api_logging_disabled_by_default(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test that API logging is disabled by default."""
        with app.app_context():
            # Clear existing logs
            db.session.query(APILogModel).delete()
            db.session.commit()

            # Make a request to a decorated endpoint without enabling logging (default behavior)
            client.post(
                "/v1.0/messages/test_message",
                json={"payload": {"key": "value"}},
                headers=self.logged_in_headers(with_super_admin_user, additional_headers={"Content-Type": "application/json"}),
            )

            # No logs should be created when logging is disabled by default
            logs = db.session.query(APILogModel).all()
            assert len(logs) == 0
