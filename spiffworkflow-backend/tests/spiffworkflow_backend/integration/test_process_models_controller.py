import io
from hashlib import sha256

from flask.app import Flask
from flask.testing import FlaskClient
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.spec_file_service import SpecFileService

from tests.spiffworkflow_backend.helpers.base_test import BaseTest


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

        user_one = self.create_user_with_permission(
            username="user_one", target_uri="/v1.0/process-groups/caller:*"
        )
        self.add_permissions_to_user(
            user=user_one, target_uri="/v1.0/process-models/caller:*", permission_names=["create", "read", "update"]
        )
        assert process_model.primary_file_name is not None
        bpmn_file_data_bytes = SpecFileService.get_data(process_model, process_model.primary_file_name)
        file_contents_hash = sha256(bpmn_file_data_bytes).hexdigest()

        data = {"file": (io.BytesIO(bpmn_file_data_bytes), process_model.primary_file_name)}
        url = f"/v1.0/process-models/{process_model.modified_process_model_identifier()}/files/{process_model.primary_file_name}?file_contents_hash={file_contents_hash}"
        response = client.put(
            url,
            data=data,
            follow_redirects=True,
            content_type="multipart/form-data",
            headers=self.logged_in_headers(user_one),
        )

        assert response.status_code == 403
        assert response.json is not None
        assert response.json['message'].startswith("NotAuthorizedError: You are not authorized to use one or more processes as a called element")
