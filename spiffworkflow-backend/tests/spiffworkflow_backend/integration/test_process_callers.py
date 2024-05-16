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
