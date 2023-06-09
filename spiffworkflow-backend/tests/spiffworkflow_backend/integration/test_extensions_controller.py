from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from spiffworkflow_backend.models.user import UserModel
from flask.testing import FlaskClient
from flask.app import Flask

class TestExtensionsController(BaseTest):
    def test_basic_extension(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        process_model_identifier = self.create_group_and_model_with_bpmn(
            client=client,
            user=with_super_admin_user,
            process_group_id="runs_without_input",
            process_model_id="sample",
            bpmn_file_name=None,
            bpmn_file_location="sample",
        )

        response = client.post(
            f"/v1.0/extensions/{self.modify_process_identifier_for_path_param(process_model_identifier)}",
            headers=self.logged_in_headers(with_super_admin_user),
        )

        expected_task_data = {'Mike': 'Awesome', 'my_var': 'Hello World', 'person': 'Kevin', 'validate_only': False, 'wonderfulness': 'Very wonderful'}
        assert response.json is not None
        import pdb; pdb.set_trace()
        assert response.json == expected_task_data
