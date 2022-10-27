import json

from spiffworkflow_backend.models.process_group import ProcessGroup, ProcessGroupSchema
from spiffworkflow_backend.models.process_model import ProcessModelInfo, ProcessModelInfoSchema
from spiffworkflow_backend.models.user import UserModel
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from flask.app import Flask
from flask.testing import FlaskClient


class TestNestedGroups(BaseTest):

    def test_nested_groups(
            self,
            app: Flask,
            client: FlaskClient,
            with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        # /process-groups/{process_group_path}/show
        target_uri = "/v1.0/process-groups/group_a,group_b/show"
        user = self.find_or_create_user()
        self.add_permissions_to_user(
            user, target_uri=target_uri, permission_names=["read"]
        )
        response = client.get(
            target_uri,
            headers=self.logged_in_headers(user)
        )
        print("test_nested_groups")

    def test_add_nested_group(
            self,
            app: Flask,
            client: FlaskClient,
            with_db_and_bpmn_file_cleanup: None,
            with_super_admin_user: UserModel,
    ) -> None:
        target_uri = "/process-groups"
        # user = self.find_or_create_user()
        # self.add_permissions_to_user(
        #     user, target_uri=target_uri, permission_names=["read", "create"]
        # )
        process_group_a = ProcessGroup(
            id="group_a",
            display_name="Group A",
            display_order=0,
            admin=False,
        )
        response_a = client.post(
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
        response_b = client.post(
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
        response_c = client.post(
            "/v1.0/process-groups",
            headers=self.logged_in_headers(with_super_admin_user),
            content_type="application/json",
            data=json.dumps(ProcessGroupSchema().dump(process_group_c)),
        )

        print("test_add_nested_group")

    def test_process_model_add(
            self,
            app: Flask,
            client: FlaskClient,
            with_db_and_bpmn_file_cleanup: None,
            with_super_admin_user: UserModel,
    ):
        process_group_a = ProcessGroup(
            id="group_a",
            display_name="Group A",
            display_order=0,
            admin=False,
        )
        response_a = client.post(
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
        response_b = client.post(
            "/v1.0/process-groups",
            headers=self.logged_in_headers(with_super_admin_user),
            content_type="application/json",
            data=json.dumps(ProcessGroupSchema().dump(process_group_b)),
        )
        process_model = ProcessModelInfo(
            id="process_model",
            display_name="Process Model",
            description="Process Model",
            process_group_id="group_a/group_b",
            primary_file_name="primary_file.bpmn",
            primary_process_id="primary_process_id",
            display_order=0
        )
        model_response = client.post(
            "v1.0/process-models",
            headers=self.logged_in_headers(with_super_admin_user),
            content_type="application/json",
            data=json.dumps(ProcessModelInfoSchema().dump(process_model))
        )
        print("test_process_model_add")
