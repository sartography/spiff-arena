"""Test_users_controller."""
from flask.app import Flask
from flask.testing import FlaskClient
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec

from spiffworkflow_backend.models.user import UserModel


class TestProcessInstancesController(BaseTest):
    """TestProcessInstancesController."""

    def test_find_by_id(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_user_search_returns_a_user."""
        user_one = self.create_user_with_permission(
            username="user_one", target_uri="/process-instances/find-by-id/*"
        )
        user_two = self.create_user_with_permission(
            username="user_two", target_uri="/process-instances/find-by-id/*"
        )

        process_model = load_test_spec(
            process_model_id="group/sample",
            bpmn_file_name="sample.bpmn",
            process_model_source_directory="sample",
        )
        process_instance = self.create_process_instance_from_process_model(
            process_model=process_model, user=user_one
        )

        response = client.get(
            f"/v1.0/process-instances/find-by-id/{process_instance.id}",
            headers=self.logged_in_headers(user_one),
        )
        assert response.status_code == 200
        assert response.json
        assert 'process_instance' in response.json
        assert response.json['process_instance']["id"] == process_instance.id
        assert response.json['uri_type'] == 'for-me'

        response = client.get(
            f"/v1.0/process-instances/find-by-id/{process_instance.id}",
            headers=self.logged_in_headers(user_two),
        )
        assert response.status_code == 400

        response = client.get(
            f"/v1.0/process-instances/find-by-id/{process_instance.id}",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200
        assert response.json
        assert 'process_instance' in response.json
        assert response.json['process_instance']["id"] == process_instance.id
        assert response.json['uri_type'] is None
