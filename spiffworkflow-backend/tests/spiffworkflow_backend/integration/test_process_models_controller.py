import io
from hashlib import sha256

from flask.app import Flask
from flask.testing import FlaskClient
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.spec_file_service import SpecFileService

from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestProcessModelsController(BaseTest):
    def test_cannot_save_process_model_file_with_called_elements_user_does_not_have_access_to(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        process_model = self.create_group_and_model_with_bpmn(
            client=client,
            user=with_super_admin_user,
            process_group_id="caller",
            process_model_id="caller",
            bpmn_file_location="call_activity_same_directory",
            bpmn_file_name="call_activity_test.bpmn",
        )
        self.create_group_and_model_with_bpmn(
            client=client,
            user=with_super_admin_user,
            process_group_id="callee",
            process_model_id="callee",
            bpmn_file_location="call_activity_same_directory",
            bpmn_file_name="callable_process.bpmn",
        )

        user_one = self.create_user_with_permission(username="user_one", target_uri="/v1.0/process-groups/caller:*")
        self.add_permissions_to_user(
            user=user_one, target_uri="/v1.0/process-models/caller:*", permission_names=["create", "read", "update"]
        )
        assert process_model.primary_file_name is not None
        bpmn_file_data_bytes = SpecFileService.get_data(process_model, process_model.primary_file_name)
        file_contents_hash = sha256(bpmn_file_data_bytes).hexdigest()

        data = {"file": (io.BytesIO(bpmn_file_data_bytes), process_model.primary_file_name)}
        url = (
            f"/v1.0/process-models/{process_model.modified_process_model_identifier()}/files/"
            f"{process_model.primary_file_name}?file_contents_hash={file_contents_hash}"
        )
        response = client.put(
            url,
            data=data,
            follow_redirects=True,
            content_type="multipart/form-data",
            headers=self.logged_in_headers(user_one),
        )

        assert response.status_code == 403
        assert response.json is not None
        assert response.json["message"].startswith(
            "NotAuthorizedError: You are not authorized to use one or more processes as a called element"
        )

    def test_process_model_show(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        user = BaseTest.create_user_with_permission("super_admin")
        process_model_1 = load_test_spec(
            "test_group/hello_world",
            bpmn_file_name="hello_world.bpmn",
            process_model_source_directory="hello_world",
        )
        process_model_2 = load_test_spec(
            "non_executable/non_executable",
            bpmn_file_name="non_executable.bpmn",
            process_model_source_directory="non_executable",
        )
        json = self._get_process_show_show_response(client, user, process_model_1.modified_process_model_identifier())
        assert json["is_executable"] is True

        json = self._get_process_show_show_response(client, user, process_model_2.modified_process_model_identifier())
        assert json["is_executable"] is False

    def _get_process_show_show_response(self, client: FlaskClient, user: UserModel, process_model_id: str) -> dict:
        url = f"/v1.0/process-models/{process_model_id}"
        response = client.get(
            url,
            follow_redirects=True,
            headers=self.logged_in_headers(user),
        )
        assert response.status_code == 200
        assert response.json is not None
        hot_dict: dict = response.json
        return hot_dict
