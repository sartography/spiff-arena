import re

from flask.app import Flask
from flask.testing import FlaskClient
from spiffworkflow_backend.models.user import UserModel

from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestExtensionsController(BaseTest):
    def test_basic_extension(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        process_model = self.create_group_and_model_with_bpmn(
            client=client,
            user=with_super_admin_user,
            process_group_id="runs_without_input",
            process_model_id="sample",
            bpmn_file_location="sample",
        )

        response = client.post(
            f"/v1.0/extensions/{self.modify_process_identifier_for_path_param(process_model.id)}",
            headers=self.logged_in_headers(with_super_admin_user),
        )

        expected_task_data = {
            "Mike": "Awesome",
            "my_var": "Hello World",
            "person": "Kevin",
            "validate_only": False,
            "wonderfulness": "Very wonderful",
        }
        assert response.json is not None
        assert response.json == expected_task_data

    def test_extension_can_run_without_restriction(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        process_model = self.create_group_and_model_with_bpmn(
            client=client,
            user=with_super_admin_user,
            process_group_id="runs_without_input",
            process_model_id="script_task_with_import",
            bpmn_file_location="script_task_with_import",
        )

        response = client.post(
            f"/v1.0/extensions/{self.modify_process_identifier_for_path_param(process_model.id)}",
            headers=self.logged_in_headers(with_super_admin_user),
        )

        assert response.json is not None
        assert "pi_json" in response.json
        assert "id" in response.json["pi_json"]
        assert re.match(r"^\d+$", str(response.json["pi_json"]["id"]))
