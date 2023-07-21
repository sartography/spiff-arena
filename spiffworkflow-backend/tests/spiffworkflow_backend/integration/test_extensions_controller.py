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
        with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_EXTENSIONS_API_ENABLED", True):
            process_model = self.create_group_and_model_with_bpmn(
                client=client,
                user=with_super_admin_user,
                process_group_id="extensions",
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

    def test_returns_403_if_extensions_not_enabled(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_EXTENSIONS_API_ENABLED", False):
            process_model = self.create_group_and_model_with_bpmn(
                client=client,
                user=with_super_admin_user,
                process_group_id="extensions",
                process_model_id="sample",
                bpmn_file_location="sample",
            )

            response = client.post(
                f"/v1.0/extensions/{self.modify_process_identifier_for_path_param(process_model.id)}",
                headers=self.logged_in_headers(with_super_admin_user),
            )
            assert response.status_code == 403
            assert response.json
            assert response.json["error_code"] == "extensions_api_not_enabled"

    def test_returns_403_if_process_model_does_not_match_configured_prefix(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_EXTENSIONS_API_ENABLED", True):
            process_model = self.create_group_and_model_with_bpmn(
                client=client,
                user=with_super_admin_user,
                process_group_id="extensions_not_it",
                process_model_id="sample",
                bpmn_file_location="sample",
            )

            response = client.post(
                f"/v1.0/extensions/{self.modify_process_identifier_for_path_param(process_model.id)}",
                headers=self.logged_in_headers(with_super_admin_user),
            )
            assert response.status_code == 403
            assert response.json
            assert response.json["error_code"] == "invalid_process_model_extension"

    def test_extension_can_run_without_restriction(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_EXTENSIONS_API_ENABLED", True):
            process_model = self.create_group_and_model_with_bpmn(
                client=client,
                user=with_super_admin_user,
                process_group_id="extensions",
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
