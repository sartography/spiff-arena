from flask import Flask
from starlette.testclient import TestClient

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.user import UserModel
from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestHumanTaskMetadata(BaseTest):
    def test_json_metadata_population(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        process_group_id = "test_group"
        process_model_id = "human_task_metadata"
        bpmn_file_location = "human_task_metadata"

        process_model = self.create_group_and_model_with_bpmn(
            client,
            with_super_admin_user,
            process_group_id=process_group_id,
            process_model_id=process_model_id,
            bpmn_file_location=bpmn_file_location,
        )

        headers = self.logged_in_headers(with_super_admin_user)
        response = self.create_process_instance_from_process_model_id_with_api(client, process_model.id, headers)
        assert response.status_code == 201
        process_instance_id = response.json()["id"]

        response = client.post(
            f"/v1.0/process-instances/{self.modify_process_identifier_for_path_param(process_model.id)}/{process_instance_id}/run",
            headers=headers,
        )
        assert response.status_code == 200

        # Verify HumanTaskModel
        human_tasks = db.session.query(HumanTaskModel).filter(HumanTaskModel.process_instance_id == process_instance_id).all()
        assert len(human_tasks) == 1
        human_task = human_tasks[0]

        assert human_task.json_metadata is not None
        assert human_task.json_metadata["dynamic_key"] == "dynamic_value"
        assert human_task.json_metadata["static_key"] == "static_value"

    def test_json_metadata_error_handling(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        process_group_id = "test_group"
        process_model_id = "human_task_metadata_error"
        bpmn_file_location = "human_task_metadata_error"

        process_model = self.create_group_and_model_with_bpmn(
            client,
            with_super_admin_user,
            process_group_id=process_group_id,
            process_model_id=process_model_id,
            bpmn_file_location=bpmn_file_location,
        )

        headers = self.logged_in_headers(with_super_admin_user)
        response = self.create_process_instance_from_process_model_id_with_api(client, process_model.id, headers)
        assert response.status_code == 201
        process_instance_id = response.json()["id"]

        response = client.post(
            f"/v1.0/process-instances/{self.modify_process_identifier_for_path_param(process_model.id)}/{process_instance_id}/run",
            headers=headers,
        )
        assert response.status_code == 200

        human_tasks = db.session.query(HumanTaskModel).filter(HumanTaskModel.process_instance_id == process_instance_id).all()
        assert len(human_tasks) == 1
        human_task = human_tasks[0]

        assert human_task.json_metadata is not None
        assert "dynamic_key_error" in human_task.json_metadata
        error_message = human_task.json_metadata["dynamic_key_error"]
        assert "Failed to evaluate taskMetadataValue dynamic_key:" in error_message
