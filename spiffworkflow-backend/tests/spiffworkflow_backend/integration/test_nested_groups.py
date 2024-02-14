import json

from flask.app import Flask
from flask.testing import FlaskClient
from spiffworkflow_backend.models.process_group import ProcessGroup
from spiffworkflow_backend.models.process_group import ProcessGroupSchema
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.models.process_model import ProcessModelInfoSchema
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService

from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestNestedGroups(BaseTest):
    def test_delete_group_with_running_instance(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        process_group_id = "test_group"
        process_model_id = "manual_task"
        bpmn_file_name = "manual_task.bpmn"
        bpmn_file_location = "manual_task"
        process_model = self.create_group_and_model_with_bpmn(
            client,
            with_super_admin_user,
            process_group_id=process_group_id,
            process_model_id=process_model_id,
            bpmn_file_name=bpmn_file_name,
            bpmn_file_location=bpmn_file_location,
        )
        response = self.create_process_instance_from_process_model_id_with_api(
            client,
            process_model.id,
            self.logged_in_headers(with_super_admin_user),
        )
        process_instance_id = response.json["id"]

        client.post(
            f"/v1.0/process-instances/{self.modify_process_identifier_for_path_param(process_model.id)}/{process_instance_id}/run",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        process_instance = ProcessInstanceService().get_process_instance(process_instance_id)
        assert process_instance
        modified_process_group_id = process_group_id.replace("/", ":")
        response = client.delete(
            f"/v1.0/process-groups/{modified_process_group_id}",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 400
        assert response.json["error_code"] == "existing_instances"
        assert "We cannot delete the group" in response.json["message"]
        assert "there are models with existing instances inside the group" in response.json["message"]

    def test_delete_group_with_running_instance_in_nested_group(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        process_group_a = ProcessGroup(
            id="group_a",
            display_name="Group A",
            display_order=0,
            admin=False,
        )
        response_a = client.post(  # noqa: F841
            "/v1.0/process-groups",
            headers=self.logged_in_headers(with_super_admin_user),
            content_type="application/json",
            data=json.dumps(ProcessGroupSchema().dump(process_group_a)),
        )

        process_group_id = "group_a/test_group"
        process_model_id = "manual_task"
        bpmn_file_name = "manual_task.bpmn"
        bpmn_file_location = "manual_task"
        process_model = self.create_group_and_model_with_bpmn(
            client,
            with_super_admin_user,
            process_group_id=process_group_id,
            process_model_id=process_model_id,
            bpmn_file_name=bpmn_file_name,
            bpmn_file_location=bpmn_file_location,
        )
        response = self.create_process_instance_from_process_model_id_with_api(
            client,
            process_model.id,
            self.logged_in_headers(with_super_admin_user),
        )
        process_instance_id = response.json["id"]

        client.post(
            f"/v1.0/process-instances/{process_instance_id}/run",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        process_instance = ProcessInstanceService().get_process_instance(process_instance_id)
        assert process_instance
        modified_process_group_id = process_group_id.replace("/", ":")
        response = client.delete(
            f"/v1.0/process-groups/{modified_process_group_id}",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 400
        assert response.json["error_code"] == "existing_instances"
        assert "We cannot delete the group" in response.json["message"]
        assert "there are models with existing instances inside the group" in response.json["message"]

    def test_nested_groups(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        # /process-groups/{process_group_path}/show
        target_uri = "/v1.0/process-groups/group_a,group_b"
        user = self.find_or_create_user()
        self.add_permissions_to_user(user, target_uri=target_uri, permission_names=["read"])
        response = client.get(target_uri, headers=self.logged_in_headers(user))  # noqa: F841

    def test_add_nested_group(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        process_group_a = ProcessGroup(
            id="group_a",
            display_name="Group A",
            display_order=0,
            admin=False,
        )
        response_a = client.post(  # noqa: F841
            "/v1.0/process-groups",
            headers=self.logged_in_headers(with_super_admin_user),
            content_type="application/json",
            data=json.dumps(ProcessGroupSchema().dump(process_group_a)),
        )
        process_group_b = ProcessGroup(
            id="group_a/group_b",
            display_name="Group B",
            display_order=0,
            admin=False,
        )
        response_b = client.post(  # noqa: F841
            "/v1.0/process-groups",
            headers=self.logged_in_headers(with_super_admin_user),
            content_type="application/json",
            data=json.dumps(ProcessGroupSchema().dump(process_group_b)),
        )
        process_group_c = ProcessGroup(
            id="group_a/group_b/group_c",
            display_name="Group C",
            display_order=0,
            admin=False,
        )
        response_c = client.post(  # noqa: F841
            "/v1.0/process-groups",
            headers=self.logged_in_headers(with_super_admin_user),
            content_type="application/json",
            data=json.dumps(ProcessGroupSchema().dump(process_group_c)),
        )

    def test_process_model_create_nested(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        process_group_a = ProcessGroup(
            id="group_a",
            display_name="Group A",
            display_order=0,
            admin=False,
        )
        response_a = client.post(  # noqa: F841
            "/v1.0/process-groups",
            headers=self.logged_in_headers(with_super_admin_user),
            content_type="application/json",
            data=json.dumps(ProcessGroupSchema().dump(process_group_a)),
        )
        process_group_b = ProcessGroup(
            id="group_a/group_b",
            display_name="Group B",
            display_order=0,
            admin=False,
        )
        response_b = client.post(  # noqa: F841
            "/v1.0/process-groups",
            headers=self.logged_in_headers(with_super_admin_user),
            content_type="application/json",
            data=json.dumps(ProcessGroupSchema().dump(process_group_b)),
        )
        process_model = ProcessModelInfo(
            id="process_model",
            display_name="Process Model",
            description="Process Model",
            primary_file_name="primary_file.bpmn",
            primary_process_id="primary_process_id",
            display_order=0,
        )
        model_response = client.post(  # noqa: F841
            "v1.0/process-models",
            headers=self.logged_in_headers(with_super_admin_user),
            content_type="application/json",
            data=json.dumps(ProcessModelInfoSchema().dump(process_model)),
        )

    def test_process_group_show(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        # target_uri = "/process-groups/{process_group_id}"
        # user = self.find_or_create_user("testadmin1")
        # self.add_permissions_to_user(
        #     user, target_uri="v1.0/process-groups", permission_names=["read", "create"]
        # )
        # self.add_permissions_to_user(
        #     user, target_uri="/process-groups/{process_group_id}", permission_names=["read", "create"]
        # )

        process_group_a = ProcessGroup(
            id="group_a",
            display_name="Group A",
            display_order=0,
            admin=False,
        )
        response_create_a = client.post(  # noqa: F841
            "/v1.0/process-groups",
            headers=self.logged_in_headers(with_super_admin_user),
            content_type="application/json",
            data=json.dumps(ProcessGroupSchema().dump(process_group_a)),
        )

        target_uri = "/v1.0/process-groups/group_a"
        user = self.find_or_create_user()
        self.add_permissions_to_user(user, target_uri=target_uri, permission_names=["read"])
        response = client.get(target_uri, headers=self.logged_in_headers(user))  # noqa: F841
