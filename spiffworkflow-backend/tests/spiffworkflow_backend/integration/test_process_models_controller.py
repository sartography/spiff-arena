import io
import json
from hashlib import sha256
from unittest.mock import patch

from flask.app import Flask
from flask.testing import FlaskClient
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
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
        self.create_group_and_model_with_bpmn(
            client=client,
            user=with_super_admin_user,
            process_group_id="callee",
            process_model_id="callee",
            bpmn_file_location="call_activity_same_directory",
            bpmn_file_name="callable_process.bpmn",
        )
        process_model = self.create_group_and_model_with_bpmn(
            client=client,
            user=with_super_admin_user,
            process_group_id="caller",
            process_model_id="caller",
            bpmn_file_location="call_activity_same_directory",
            bpmn_file_name="call_activity_test.bpmn",
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
        process_model_1 = load_test_spec(
            "test_group/hello_world",
            bpmn_file_name="hello_world.bpmn",
            process_model_source_directory="hello_world",
        )
        process_model_2 = load_test_spec(
            "test_group/non_executable",
            bpmn_file_name="non_executable.bpmn",
            process_model_source_directory="non_executable",
        )
        json = self._get_process_show_show_response(
            client, with_super_admin_user, process_model_1.modified_process_model_identifier()
        )
        assert json["id"] == "test_group/hello_world"
        assert json["is_executable"] is True

        json = self._get_process_show_show_response(
            client, with_super_admin_user, process_model_2.modified_process_model_identifier()
        )
        assert json["id"] == "test_group/non_executable"
        assert json["is_executable"] is False

    def test_process_model_show_when_not_found(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        json = self._get_process_show_show_response(
            client, with_super_admin_user, "bad-model-does-not-exist", expected_response=400
        )
        assert json["error_code"] == "process_model_cannot_be_found"

    def test_process_model_test_generate(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        process_model = load_test_spec(
            process_model_id="test_group/with-service-task-call-activity-sub-process",
            process_model_source_directory="with-service-task-call-activity-sub-process",
        )
        process_instance = self.create_process_instance_from_process_model(process_model, user=with_super_admin_user)
        process_instance_id = process_instance.id
        processor = ProcessInstanceProcessor(process_instance)
        connector_response = {
            "body": '{"ok": true}',
            "mimetype": "application/json",
            "http_status": 200,
            "operator_identifier": "http/GetRequestV2",
        }
        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.ok = True
            mock_post.return_value.text = json.dumps(connector_response)
            processor.do_engine_steps(save=True)

        self.complete_next_manual_task(processor, execution_mode="synchronous")
        self.complete_next_manual_task(processor, execution_mode="synchronous", data={"firstName": "Chuck"})
        process_instance = ProcessInstanceModel.query.filter_by(id=process_instance_id).first()
        assert process_instance.status == ProcessInstanceStatus.complete.value

        url = f"/v1.0/process-model-tests/create/{process_model.modified_process_model_identifier()}"
        response = client.post(
            url,
            headers=self.logged_in_headers(with_super_admin_user),
            content_type="application/json",
            data=json.dumps({"process_instance_id": process_instance_id}),
        )
        assert response.status_code == 200

        test_case_identifier = f"test_case_for_process_instance_{process_instance_id}"
        expected_specification = {
            test_case_identifier: {
                "tasks": {
                    "Process_sub_level:sub_manual_task": {"data": [{}]},
                    "call_activity_sub_process:sub_level_sub_process_user_task": {"data": [{"firstName": "Chuck"}]},
                    "Process_top_level:top_service_task": {
                        "data": [
                            {
                                "backend_status_response": {
                                    "body": '{"ok": true}',
                                    "mimetype": "application/json",
                                    "http_status": 200,
                                    "operator_identifier": "http/GetRequestV2",
                                }
                            }
                        ]
                    },
                },
                "expected_output_json": {
                    "firstName": "Chuck",
                    "data_objects": {"top_level_data_object": "a"},
                    "backend_status_response": {
                        "body": '{"ok": true}',
                        "mimetype": "application/json",
                        "http_status": 200,
                        "operator_identifier": "http/GetRequestV2",
                    },
                },
            }
        }
        assert expected_specification == response.json

    def _get_process_show_show_response(
        self, client: FlaskClient, user: UserModel, process_model_id: str, expected_response: int = 200
    ) -> dict:
        url = f"/v1.0/process-models/{process_model_id}"
        response = client.get(
            url,
            follow_redirects=True,
            headers=self.logged_in_headers(user),
        )
        assert response.status_code == expected_response
        assert response.json is not None
        process_model_data: dict = response.json
        return process_model_data
