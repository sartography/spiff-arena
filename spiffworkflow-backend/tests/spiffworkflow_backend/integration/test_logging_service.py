"""Test_logging_service."""
from flask.app import Flask
from flask.testing import FlaskClient
from spiffworkflow_backend.models.user import UserModel
from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestLoggingService(BaseTest):
    """Test logging service."""

    def test_logging_service_spiff_logger(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_process_instance_run."""
        process_group_id = "test_logging_spiff_logger"
        process_model_id = "simple_script"
        headers = self.logged_in_headers(with_super_admin_user)
        response = self.create_process_instance(
            client, process_group_id, process_model_id, headers
        )
        assert response.json is not None
        process_instance_id = response.json["id"]
        response = client.post(
            f"/v1.0/process-models/{process_group_id}/{process_model_id}/process-instances/{process_instance_id}/run",
            headers=headers,
        )
        assert response.status_code == 200

        log_response = client.get(
            f"/v1.0/process-models/{process_group_id}/{process_model_id}/process-instances/{process_instance_id}/logs",
            headers=headers,
        )
        assert log_response.status_code == 200
        assert log_response.json
        logs: list = log_response.json["results"]
        assert len(logs) > 0
        for log in logs:
            assert log["process_instance_id"] == process_instance_id
            for key in [
                "timestamp",
                "spiff_task_guid",
                "bpmn_task_identifier",
                "bpmn_process_identifier",
                "message",
            ]:
                assert key in log.keys()
