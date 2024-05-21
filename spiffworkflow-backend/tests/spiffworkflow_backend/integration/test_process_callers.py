import os

from flask.app import Flask
from flask.testing import FlaskClient
from spiffworkflow_backend.models.task import TaskModel  # noqa: F401
from spiffworkflow_backend.models.user import UserModel

from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestProcessCallers(BaseTest):
    def test_references_after_process_model_create(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        self.create_group_and_model_with_bpmn(
            client=client,
            user=with_super_admin_user,
            process_group_id="test_group_two",
            process_model_id="call_activity_nested",
            bpmn_file_location="call_activity_nested",
        )

        response = client.get(
            "/v1.0/processes",
            headers=self.logged_in_headers(with_super_admin_user),
        )

        assert response.status_code == 200
        assert response.json is not None
        assert isinstance(response.json, list)
        assert len(response.json) == 4

        response = client.get(
            "/v1.0/processes/callers/Level2",
            headers=self.logged_in_headers(with_super_admin_user),
        )

        assert response.status_code == 200
        assert response.json is not None
        assert isinstance(response.json, list)
        assert len(response.json) == 1

    def test_references_after_process_model_delete(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        self.create_group_and_model_with_bpmn(
            client=client,
            user=with_super_admin_user,
            process_group_id="test_group_two",
            process_model_id="call_activity_nested",
            bpmn_file_location="call_activity_nested",
        )

        response = client.delete(
            "/v1.0/process-models/test_group_two:call_activity_nested",
            headers=self.logged_in_headers(with_super_admin_user),
        )

        assert response.status_code == 200

        response = client.get(
            "/v1.0/processes",
            headers=self.logged_in_headers(with_super_admin_user),
        )

        assert response.status_code == 200
        assert response.json is not None
        assert isinstance(response.json, list)
        assert len(response.json) == 0

        response = client.get(
            "/v1.0/processes/callers/Level2",
            headers=self.logged_in_headers(with_super_admin_user),
        )

        assert response.status_code == 200
        assert response.json is not None
        assert isinstance(response.json, list)
        assert len(response.json) == 0

    def test_references_after_process_group_delete(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        self.create_group_and_model_with_bpmn(
            client=client,
            user=with_super_admin_user,
            process_group_id="test_group_two",
            process_model_id="call_activity_nested",
            bpmn_file_location="call_activity_nested",
        )

        response = client.delete(
            "/v1.0/process-groups/test_group_two",
            headers=self.logged_in_headers(with_super_admin_user),
        )

        assert response.status_code == 200

        response = client.get(
            "/v1.0/processes",
            headers=self.logged_in_headers(with_super_admin_user),
        )

        assert response.status_code == 200
        assert response.json is not None
        assert isinstance(response.json, list)
        assert len(response.json) == 0

        response = client.get(
            "/v1.0/processes/callers/Level2",
            headers=self.logged_in_headers(with_super_admin_user),
        )

        assert response.status_code == 200
        assert response.json is not None
        assert isinstance(response.json, list)
        assert len(response.json) == 0

    def test_references_after_process_file_delete(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        self.create_group_and_model_with_bpmn(
            client=client,
            user=with_super_admin_user,
            process_group_id="test_group_two",
            process_model_id="call_activity_nested",
            bpmn_file_location="call_activity_nested",
        )

        response = client.delete(
            "/v1.0/process-models/test_group_two:call_activity_nested/files/call_activity_level_2.bpmn",
            headers=self.logged_in_headers(with_super_admin_user),
        )

        assert response.status_code == 200

        response = client.get(
            "/v1.0/processes",
            headers=self.logged_in_headers(with_super_admin_user),
        )

        assert response.status_code == 200
        assert response.json is not None
        assert isinstance(response.json, list)
        assert len(response.json) == 3

        response = client.get(
            "/v1.0/processes/callers/Level2",
            headers=self.logged_in_headers(with_super_admin_user),
        )

        assert response.status_code == 200
        assert response.json is not None
        assert isinstance(response.json, list)
        assert len(response.json) == 0

    def test_references_after_process_file_delete_and_upload(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        process_model = self.create_group_and_model_with_bpmn(
            client=client,
            user=with_super_admin_user,
            process_group_id="test_group_two",
            process_model_id="call_activity_nested",
            bpmn_file_location="call_activity_nested",
        )

        response = client.delete(
            "/v1.0/process-models/test_group_two:call_activity_nested/files/call_activity_level_2.bpmn",
            headers=self.logged_in_headers(with_super_admin_user),
        )

        assert response.status_code == 200

        with open(f"{os.getcwd()}/tests/data/call_activity_nested/call_activity_level_2.bpmn", "rb") as f:
            file_data = f.read()

        bpmn_file_name = "call_activity_level_2.bpmn"
        bpmn_file_location = "call_activity_level_2"

        response = self.create_spec_file(
            client,
            process_model_id=process_model.id,
            process_model=process_model,
            process_model_location=bpmn_file_location,
            file_name=bpmn_file_name,
            file_data=file_data,
            user=with_super_admin_user,
        )

        assert response["process_model_id"] == process_model.id
        assert response["name"] == bpmn_file_name
        assert bytes(str(response["file_contents"]), "utf-8") == file_data

        response = client.get(
            "/v1.0/processes/callers/Level2",
            headers=self.logged_in_headers(with_super_admin_user),
        )

        assert response.status_code == 200
        assert response.json is not None
        assert isinstance(response.json, list)
        assert len(response.json) == 1
