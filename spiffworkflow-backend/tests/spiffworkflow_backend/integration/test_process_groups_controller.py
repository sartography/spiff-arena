import json
import os

import pytest
from flask.app import Flask
from flask.testing import FlaskClient

from spiffworkflow_backend.exceptions.process_entity_not_found_error import ProcessEntityNotFoundError
from spiffworkflow_backend.models.process_group import ProcessGroup
from spiffworkflow_backend.models.task import TaskModel  # noqa: F401
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestProcessGroupsController(BaseTest):
    def test_process_group_add(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        process_group = ProcessGroup(
            id="test",
            display_name="Another Test Category",
            display_order=0,
            admin=False,
            description="Test Description",
        )
        response = client.post(
            "/v1.0/process-groups",
            headers=self.logged_in_headers(with_super_admin_user),
            content_type="application/json",
            data=json.dumps(process_group.serialized()),
        )
        assert response.status_code == 201
        assert response.json

        # Check what is returned
        result = ProcessGroup(**response.json)
        assert result is not None
        assert result.display_name == "Another Test Category"
        assert result.id == "test"
        assert result.description == "Test Description"

        # Check what is persisted
        persisted = ProcessModelService.get_process_group("test")
        assert persisted.display_name == "Another Test Category"
        assert persisted.id == "test"
        assert persisted.description == "Test Description"

    def test_process_group_delete(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        process_group_id = "test"
        process_group_display_name = "My Process Group"

        self.create_process_group_with_api(
            client,
            with_super_admin_user,
            process_group_id,
            display_name=process_group_display_name,
        )
        persisted = ProcessModelService.get_process_group(process_group_id)
        assert persisted is not None
        assert persisted.id == process_group_id

        client.delete(
            f"/v1.0/process-groups/{process_group_id}",
            headers=self.logged_in_headers(with_super_admin_user),
        )

        with pytest.raises(ProcessEntityNotFoundError):
            ProcessModelService.get_process_group(process_group_id)

    def test_process_group_update(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test Process Group Update."""
        group_id = "test_process_group"
        group_display_name = "Test Group"

        self.create_process_group_with_api(client, with_super_admin_user, group_id, display_name=group_display_name)
        process_group = ProcessModelService.get_process_group(group_id)

        assert process_group.display_name == group_display_name

        process_group.display_name = "Modified Display Name"

        response = client.put(
            f"/v1.0/process-groups/{group_id}",
            headers=self.logged_in_headers(with_super_admin_user),
            content_type="application/json",
            data=json.dumps(process_group.serialized()),
        )
        assert response.status_code == 200

        process_group = ProcessModelService.get_process_group(group_id)
        assert process_group.display_name == "Modified Display Name"

    def test_process_group_list(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        # add 5 groups
        for i in range(5):
            group_id = f"test_process_group_{i}"
            group_display_name = f"Test Group {i}"
            self.create_process_group_with_api(client, with_super_admin_user, group_id, display_name=group_display_name)

        # get all groups
        response = client.get(
            "/v1.0/process-groups",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.json is not None
        assert len(response.json["results"]) == 5
        assert response.json["pagination"]["count"] == 5
        assert response.json["pagination"]["total"] == 5
        assert response.json["pagination"]["pages"] == 1

        # get first page, one per page
        response = client.get(
            "/v1.0/process-groups?page=1&per_page=1",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.json is not None
        assert len(response.json["results"]) == 1
        assert response.json["results"][0]["id"] == "test_process_group_0"
        assert response.json["pagination"]["count"] == 1
        assert response.json["pagination"]["total"] == 5
        assert response.json["pagination"]["pages"] == 5

        # get second page, one per page
        response = client.get(
            "/v1.0/process-groups?page=2&per_page=1",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.json is not None
        assert len(response.json["results"]) == 1
        assert response.json["results"][0]["id"] == "test_process_group_1"
        assert response.json["pagination"]["count"] == 1
        assert response.json["pagination"]["total"] == 5
        assert response.json["pagination"]["pages"] == 5

        # get first page, 3 per page
        response = client.get(
            "/v1.0/process-groups?page=1&per_page=3",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.json is not None
        assert len(response.json["results"]) == 3
        assert response.json["results"][0]["id"] == "test_process_group_0"
        assert response.json["results"][1]["id"] == "test_process_group_1"
        assert response.json["results"][2]["id"] == "test_process_group_2"
        assert response.json["pagination"]["count"] == 3
        assert response.json["pagination"]["total"] == 5
        assert response.json["pagination"]["pages"] == 2

        # get second page, 3 per page
        response = client.get(
            "/v1.0/process-groups?page=2&per_page=3",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        # there should only be 2 left
        assert response.json is not None
        assert len(response.json["results"]) == 2
        assert response.json["results"][0]["id"] == "test_process_group_3"
        assert response.json["results"][1]["id"] == "test_process_group_4"
        assert response.json["pagination"]["count"] == 2
        assert response.json["pagination"]["total"] == 5
        assert response.json["pagination"]["pages"] == 2

    def test_process_group_list_when_none(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        response = client.get(
            "/v1.0/process-groups",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200
        assert response.json is not None
        assert response.json["results"] == []

    def test_process_group_list_when_there_are_some(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        self.create_group_and_model_with_bpmn(client, with_super_admin_user)
        response = client.get(
            "/v1.0/process-groups",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200
        assert response.json is not None
        assert len(response.json["results"]) == 1
        assert response.json["pagination"]["count"] == 1
        assert response.json["pagination"]["total"] == 1
        assert response.json["pagination"]["pages"] == 1

    def test_process_group_list_when_user_has_resticted_access(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        self.create_group_and_model_with_bpmn(
            client, with_super_admin_user, process_group_id="admin_only", process_model_id="random_fact"
        )
        self.create_group_and_model_with_bpmn(
            client, with_super_admin_user, process_group_id="all_users", process_model_id="hello_world"
        )
        user_one = self.create_user_with_permission(username="user_one", target_uri="/v1.0/process-groups/all_users:*")
        self.add_permissions_to_user(user=user_one, target_uri="/v1.0/process-groups", permission_names=["read"])

        response = client.get(
            "/v1.0/process-groups",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200
        assert response.json is not None
        assert len(response.json["results"]) == 2
        assert response.json["pagination"]["count"] == 2
        assert response.json["pagination"]["total"] == 2
        assert response.json["pagination"]["pages"] == 1

        response = client.get(
            "/v1.0/process-groups",
            headers=self.logged_in_headers(user_one),
        )
        assert response.status_code == 200
        assert response.json is not None
        assert len(response.json["results"]) == 1
        assert response.json["results"][0]["id"] == "all_users"
        assert response.json["pagination"]["count"] == 1
        assert response.json["pagination"]["total"] == 1
        assert response.json["pagination"]["pages"] == 1

    def test_get_process_group_when_found(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        process_model = self.create_group_and_model_with_bpmn(client, with_super_admin_user)
        process_group_id, process_model_id = os.path.split(process_model.id)

        response = client.get(
            f"/v1.0/process-groups/{process_group_id}",
            headers=self.logged_in_headers(with_super_admin_user),
        )

        assert response.status_code == 200
        assert response.json is not None
        assert response.json["id"] == process_group_id
        assert response.json["process_models"] == []
        assert response.json["parent_groups"] == []

    def test_get_process_group_show_when_nested(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        self.create_group_and_model_with_bpmn(
            client=client,
            user=with_super_admin_user,
            process_group_id="test_group_one",
            process_model_id="simple_form",
            bpmn_file_location="simple_form",
        )

        self.create_group_and_model_with_bpmn(
            client=client,
            user=with_super_admin_user,
            process_group_id="test_group_one/test_group_two",
            process_model_id="call_activity_nested",
            bpmn_file_location="call_activity_nested",
        )

        response = client.get(
            "/v1.0/process-groups/test_group_one:test_group_two",
            headers=self.logged_in_headers(with_super_admin_user),
        )

        assert response.status_code == 200
        assert response.json is not None
        assert response.json["id"] == "test_group_one/test_group_two"
        assert response.json["parent_groups"] == [
            {
                "display_name": "test_group_one",
                "id": "test_group_one",
                "description": None,
                "process_models": [],
                "process_groups": [],
            }
        ]
