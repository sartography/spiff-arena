from flask.app import Flask
from starlette.testclient import TestClient

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.user import UserModel
from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestTaskAssignmentToEmptyGroup(BaseTest):
    def test_task_assigned_to_empty_group(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        process_group_id = "test_group"
        process_model_id = "task_assigned_to_group"
        bpmn_file_location = "task_assigned_to_group"

        # Create a group with no users
        group = GroupModel(identifier="my_group", name="My Group")
        db.session.add(group)
        db.session.commit()

        process_model = self.create_group_and_model_with_bpmn(
            client,
            with_super_admin_user,
            process_group_id=process_group_id,
            process_model_id=process_model_id,
            bpmn_file_location=bpmn_file_location,
        )

        headers = self.logged_in_headers(with_super_admin_user)
        response = self.create_process_instance_from_process_model_id_with_api(client, process_model.id, headers)
        assert response.json() is not None
        process_instance_id = response.json()["id"]

        response = client.post(
            f"/v1.0/process-instances/{self.modify_process_identifier_for_path_param(process_model.id)}/{process_instance_id}/run",
            headers=self.logged_in_headers(with_super_admin_user),
        )

        # In the original code, this would return a 500 error because of the
        # NoPotentialOwnersForTaskError.
        assert response.status_code == 200
