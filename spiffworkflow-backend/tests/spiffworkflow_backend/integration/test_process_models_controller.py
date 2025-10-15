import json
from hashlib import sha256
from unittest.mock import MagicMock
from unittest.mock import patch

from flask.app import Flask
from starlette.testclient import TestClient

from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.spec_file_service import SpecFileService
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestProcessModelsController(BaseTest):
    def test_cannot_save_process_model_file_with_called_elements_user_does_not_have_access_to(
        self,
        app: Flask,
        client: TestClient,
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

        files = [("file", (process_model.primary_file_name, bpmn_file_data_bytes))]
        url = (
            f"/v1.0/process-models/{process_model.modified_process_model_identifier()}/files/"
            f"{process_model.primary_file_name}?file_contents_hash={file_contents_hash}"
        )
        response = client.put(
            url,
            files=files,
            follow_redirects=True,
            headers=self.logged_in_headers(user_one),
        )
        assert response.status_code == 403
        assert response.json() is not None
        assert response.json()["message"].startswith(
            "NotAuthorizedError: You are not authorized to use one or more processes as a called element"
        )

    def test_process_model_show(
        self,
        app: Flask,
        client: TestClient,
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
        client: TestClient,
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
        client: TestClient,
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
            headers=self.logged_in_headers(with_super_admin_user, additional_headers={"Content-Type": "application/json"}),
            json={"process_instance_id": process_instance_id},
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
        assert expected_specification == response.json()

    def test_process_model_list_with_grouping_by_process_group(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        self.create_group_and_model_with_bpmn(
            client, with_super_admin_user, process_group_id="top_group", process_model_id="random_fact"
        )
        self.create_group_and_model_with_bpmn(
            client, with_super_admin_user, process_group_id="top_group/subgroup1", process_model_id="hello_world"
        )

        response = client.get(
            "/v1.0/process-models?group_by_process_group=true&recursive=true",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200
        assert response.json() is not None
        assert len(response.json()["results"]) == 1

        top_process_group = response.json()["results"][0]
        assert top_process_group["id"] == "top_group"
        assert top_process_group["display_name"] == "top_group"
        assert top_process_group["description"] is None

        assert len(top_process_group["process_models"]) == 1
        assert top_process_group["process_models"][0]["id"] == "top_group/random_fact"

        assert len(top_process_group["process_groups"]) == 1
        assert top_process_group["process_groups"][0]["id"] == "top_group/subgroup1"
        assert len(top_process_group["process_groups"][0]["process_groups"]) == 0
        assert len(top_process_group["process_groups"][0]["process_models"]) == 1
        assert top_process_group["process_groups"][0]["process_models"][0]["id"] == "top_group/subgroup1/hello_world"

    def test_get_process_model_when_found(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        process_model = self.create_group_and_model_with_bpmn(client, with_super_admin_user, bpmn_file_name="random_fact.bpmn")
        modified_process_model_identifier = process_model.modify_process_identifier_for_path_param(process_model.id)

        response = client.get(
            f"/v1.0/process-models/{modified_process_model_identifier}",
            headers=self.logged_in_headers(with_super_admin_user),
        )

        assert response.status_code == 200
        assert response.json() is not None
        assert response.json()["id"] == process_model.id
        assert len(response.json()["files"]) == 1
        assert response.json()["files"][0]["name"] == "random_fact.bpmn"
        assert response.json()["parent_groups"] == [
            {"display_name": "test_group", "id": "test_group", "description": None, "process_models": [], "process_groups": []}
        ]

    def test_get_process_model_when_not_found(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        process_model_dir_name = "THIS_NO_EXISTS"
        group_id = self.create_process_group_with_api(client, with_super_admin_user, "my_group")
        bad_process_model_id = f"{group_id}/{process_model_dir_name}"
        modified_bad_process_model_id = bad_process_model_id.replace("/", ":")
        response = client.get(
            f"/v1.0/process-models/{modified_bad_process_model_id}",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 400
        assert response.json() is not None
        assert response.json()["error_code"] == "process_model_cannot_be_found"

    @patch("spiffworkflow_backend.routes.process_models_controller.trigger_metadata_backfill")
    def test_process_model_update_triggers_metadata_backfill(
        self,
        mock_trigger_metadata_backfill: MagicMock,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        user = self.create_user_with_permission("test_user")
        process_model = self.create_process_model_with_metadata()
        mock_trigger_metadata_backfill.return_value = {"status": "triggered", "task_id": "test-task-id"}

        modified_process_model_identifier = process_model.id.replace("/", ":")
        new_metadata_paths = [
            {"key": "awesome_var", "path": "outer.inner"},
            {"key": "invoice_number", "path": "invoice_number"},
            {"key": "new_key", "path": "new.path"},
        ]

        response = client.put(
            f"/v1.0/process-models/{modified_process_model_identifier}",
            json={
                "metadata_extraction_paths": new_metadata_paths,
                "display_name": process_model.display_name,
                "description": process_model.description,
            },
            headers=self.logged_in_headers(user),
        )
        assert response.status_code == 200

        mock_trigger_metadata_backfill.assert_called_once()
        args, _ = mock_trigger_metadata_backfill.call_args
        _process_model_identifier, old_metadata_extraction_paths, new_metadata_extraction_paths = args

        assert len(old_metadata_extraction_paths) == 2
        assert old_metadata_extraction_paths[0]["key"] == "awesome_var"
        assert old_metadata_extraction_paths[1]["key"] == "invoice_number"

        assert len(new_metadata_extraction_paths) == 3
        assert new_metadata_extraction_paths[0]["key"] == "awesome_var"
        assert new_metadata_extraction_paths[1]["key"] == "invoice_number"
        assert new_metadata_extraction_paths[2]["key"] == "new_key"

    @patch("spiffworkflow_backend.routes.process_models_controller.trigger_metadata_backfill")
    def test_process_model_update_without_metadata_changes_does_not_trigger_backfill(
        self,
        mock_trigger_metadata_backfill: MagicMock,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        user = self.create_user_with_permission("test_user")
        process_model = self.create_process_model_with_metadata()
        modified_process_model_identifier = process_model.id.replace("/", ":")

        response = client.put(
            f"/v1.0/process-models/{modified_process_model_identifier}",
            json={
                "display_name": "Updated Display Name",
                "description": process_model.description,
            },
            headers=self.logged_in_headers(user),
        )
        assert response.status_code == 200

        mock_trigger_metadata_backfill.assert_not_called()
        updated_model = ProcessModelService.get_process_model(process_model.id)
        assert updated_model.display_name == "Updated Display Name"

    def _get_process_show_show_response(
        self, client: TestClient, user: UserModel, process_model_id: str, expected_response: int = 200
    ) -> dict:
        url = f"/v1.0/process-models/{process_model_id}"
        response = client.get(
            url,
            follow_redirects=True,
            headers=self.logged_in_headers(user),
        )
        assert response.status_code == expected_response
        assert response.json() is not None
        process_model_data: dict = response.json()
        return process_model_data

    def test_get_human_task_definitions(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        process_model = load_test_spec(
            "test_group/model_with_lanes",
            bpmn_file_name="lanes.bpmn",
            process_model_source_directory="model_with_lanes",
        )
        modified_id = process_model.modify_process_identifier_for_path_param(process_model.id)
        url = f"/v1.0/process-models/{modified_id}/human-task-definitions"
        response = client.get(url, headers=self.logged_in_headers(with_super_admin_user))
        assert response.status_code == 200
        human_tasks = response.json()
        assert len(human_tasks) == 3
        assert human_tasks[0]["bpmn_identifier"] == "initiator_one"
        assert human_tasks[0]["bpmn_name"] == "Initiator One"
        assert human_tasks[0]["typename"] == "ManualTask"
        assert human_tasks[0]["properties_json"]["lane"] == "Process Initiator"

    def test_process_model_copy(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test copying a process model."""
        process_model = self.create_group_and_model_with_bpmn(
            client=client,
            user=with_super_admin_user,
            process_group_id="test_group",
            process_model_id="hello_world",
            bpmn_file_name="hello_world.bpmn",
            process_model_source_directory="hello_world",
        )
        modified_process_model_identifier = process_model.modify_process_identifier_for_path_param(
            process_model.id
        )

        # Copy the process model
        copy_url = f"/v1.0/process-models/{modified_process_model_identifier}/copy"
        copy_data = {
            "id": "test_group/hello_world_copy",
            "display_name": "Hello World Copy",
        }
        response = client.post(
            copy_url,
            json=copy_data,
            headers=self.logged_in_headers(with_super_admin_user),
        )
        self.assertEqual(response.status_code, 201)

        # Verify that the new process model exists
        new_process_model_id = "test_group/hello_world_copy"
        modified_new_process_model_id = new_process_model_id.replace("/", ":")
        get_url = f"/v1.0/process-models/{modified_new_process_model_id}"
        response = client.get(
            get_url, headers=self.logged_in_headers(with_super_admin_user)
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], new_process_model_id)
        self.assertEqual(response.json()["display_name"], "Hello World Copy")
        self.assertEqual(len(response.json()["files"]), 1)
        self.assertEqual(response.json()["files"][0]["name"], "hello_world.bpmn")
