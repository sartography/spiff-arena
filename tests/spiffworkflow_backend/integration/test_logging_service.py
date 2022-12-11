"""Test_logging_service."""
from flask.app import Flask
from flask.testing import FlaskClient
from tests.spiffworkflow_backend.helpers.base_test import BaseTest

from spiffworkflow_backend.models.user import UserModel


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
        self.create_process_group(
            client=client, user=with_super_admin_user, process_group_id=process_group_id
        )
        process_model_identifier = f"{process_group_id}/{process_model_id}"
        # create the model
        self.create_process_model_with_api(
            client=client,
            process_model_id=process_model_identifier,
            process_model_display_name="Simple Script",
            process_model_description="Simple Script",
            user=with_super_admin_user,
        )

        bpmn_file_name = "simple_script.bpmn"
        bpmn_file_data_bytes = self.get_test_data_file_contents(
            bpmn_file_name, "simple_script"
        )
        # add bpmn to the model
        self.create_spec_file(
            client=client,
            process_model_id=process_model_identifier,
            file_name=bpmn_file_name,
            file_data=bpmn_file_data_bytes,
            user=with_super_admin_user,
        )
        headers = self.logged_in_headers(with_super_admin_user)
        response = self.create_process_instance_from_process_model_id(
            client, process_model_identifier, headers
        )
        assert response.json is not None
        process_instance_id = response.json["id"]
        response = client.post(
            f"/v1.0/process-instances/{self.modify_process_identifier_for_path_param(process_model_identifier)}/{process_instance_id}/run",
            headers=headers,
        )
        assert response.status_code == 200

        log_response = client.get(
            f"/v1.0/logs/{self.modify_process_identifier_for_path_param(process_model_identifier)}/{process_instance_id}",
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
