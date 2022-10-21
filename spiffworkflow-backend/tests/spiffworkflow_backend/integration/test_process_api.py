"""Test Process Api Blueprint."""
import io
import json
import time
from typing import Any

import pytest
from flask.app import Flask
from flask.testing import FlaskClient
from flask_bpmn.models.db import db
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec

from spiffworkflow_backend.exceptions.process_entity_not_found_error import (
    ProcessEntityNotFoundError,
)
from spiffworkflow_backend.models.active_task import ActiveTaskModel
from spiffworkflow_backend.models.process_group import ProcessGroup
from spiffworkflow_backend.models.process_group import ProcessGroupSchema
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
from spiffworkflow_backend.models.process_instance_report import (
    ProcessInstanceReportModel,
)
from spiffworkflow_backend.models.process_model import NotificationType
from spiffworkflow_backend.models.process_model import ProcessModelInfoSchema
from spiffworkflow_backend.models.task_event import TaskEventModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.file_system_service import FileSystemService
from spiffworkflow_backend.services.process_instance_processor import (
    ProcessInstanceProcessor,
)
from spiffworkflow_backend.services.process_model_service import ProcessModelService

# from spiffworkflow_backend.services.git_service import GitService


class TestProcessApi(BaseTest):
    """TestProcessAPi."""

    def test_returns_403_if_user_does_not_have_permission(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        """Test_returns_403_if_user_does_not_have_permission."""
        user = self.find_or_create_user()
        response = client.get(
            "/v1.0/process-groups",
            headers=self.logged_in_headers(user),
        )
        assert response.status_code == 403

        self.add_permissions_to_user(
            user, target_uri="/v1.0/process-groups", permission_names=["read"]
        )
        response = client.get(
            "/v1.0/process-groups",
            headers=self.logged_in_headers(user),
        )
        assert response.status_code == 200

        response = client.post(
            "/v1.0/process-groups",
            headers=self.logged_in_headers(user),
        )
        assert response.status_code == 403

    def test_permissions_check(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        """Test_permissions_check."""
        user = self.find_or_create_user()
        self.add_permissions_to_user(
            user, target_uri="/v1.0/process-groups", permission_names=["read"]
        )
        request_body = {
            "requests_to_check": {
                "/v1.0/process-groups": ["GET", "POST"],
                "/v1.0/process-models": ["GET"],
            }
        }
        expected_response_body = {
            "results": {
                "/v1.0/process-groups": {"GET": True, "POST": False},
                "/v1.0/process-models": {"GET": False},
            }
        }
        response = client.post(
            "/v1.0/permissions-check",
            headers=self.logged_in_headers(user),
            content_type="application/json",
            data=json.dumps(request_body),
        )
        assert response.status_code == 200
        assert response.json is not None
        assert response.json == expected_response_body

    def test_process_model_add(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_add_new_process_model."""
        process_model_identifier = "sample"
        model_display_name = "Sample"
        model_description = "The sample"

        self.create_process_model_with_api(
            client,
            process_model_id=process_model_identifier,
            process_model_display_name=model_display_name,
            process_model_description=model_description,
            user=with_super_admin_user,
        )
        process_model = ProcessModelService().get_process_model(
            process_model_identifier
        )
        assert model_display_name == process_model.display_name
        assert 0 == process_model.display_order
        assert 1 == len(ProcessModelService().get_process_groups())

        bpmn_file_name = "sample.bpmn"
        bpmn_file_data_bytes = self.get_test_data_file_contents(
            bpmn_file_name, "sample"
        )
        self.create_spec_file(
            client,
            file_name=bpmn_file_name,
            file_data=bpmn_file_data_bytes,
            process_model=process_model,
            user=with_super_admin_user,
        )
        process_model = ProcessModelService().get_process_model(
            process_model_identifier
        )
        assert process_model.primary_file_name == bpmn_file_name
        assert process_model.primary_process_id == "sample"

    def test_primary_process_id_updates_via_xml(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_primary_process_id_updates_via_xml."""
        process_model_identifier = "sample"
        initial_primary_process_id = "sample"
        terminal_primary_process_id = "new_process_id"

        process_model = load_test_spec(process_model_id=process_model_identifier)
        assert process_model.primary_process_id == initial_primary_process_id

        bpmn_file_name = "sample.bpmn"
        bpmn_file_data_bytes = self.get_test_data_file_contents(
            bpmn_file_name, "sample"
        )
        bpmn_file_data_string = bpmn_file_data_bytes.decode("utf-8")
        old_string = f'bpmn:process id="{initial_primary_process_id}"'
        new_string = f'bpmn:process id="{terminal_primary_process_id}"'
        updated_bpmn_file_data_string = bpmn_file_data_string.replace(
            old_string, new_string
        )
        updated_bpmn_file_data_bytes = bytearray(updated_bpmn_file_data_string, "utf-8")
        data = {"file": (io.BytesIO(updated_bpmn_file_data_bytes), bpmn_file_name)}

        response = client.put(
            f"/v1.0/process-models/{process_model.process_group_id}/{process_model.id}/files/{bpmn_file_name}",
            data=data,
            follow_redirects=True,
            content_type="multipart/form-data",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200
        process_model = ProcessModelService().get_process_model(
            process_model_identifier
        )
        assert process_model.primary_file_name == bpmn_file_name
        assert process_model.primary_process_id == terminal_primary_process_id

    def test_process_model_delete(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_process_model_delete."""
        self.create_process_model_with_api(
            client,
            user=with_super_admin_user,
        )

        # assert we have a model
        process_model = ProcessModelService().get_process_model("make_cookies")
        assert process_model is not None
        assert process_model.id == "make_cookies"

        # delete the model
        response = client.delete(
            f"/v1.0/process-models/{process_model.process_group_id}/{process_model.id}",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200
        assert response.json is not None
        assert response.json["ok"] is True

        # assert we no longer have a model
        with pytest.raises(ProcessEntityNotFoundError):
            ProcessModelService().get_process_model("make_cookies")

    def test_process_model_delete_with_instances(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_process_model_delete_with_instances."""
        test_process_group_id = "runs_without_input"
        test_process_model_id = "sample"
        headers = self.logged_in_headers(with_super_admin_user)
        # create an instance from a model
        response = self.create_process_instance(
            client, test_process_group_id, test_process_model_id, headers
        )

        data = json.loads(response.get_data(as_text=True))
        # make sure the instance has the correct model
        assert data["process_model_identifier"] == test_process_model_id

        # try to delete the model
        response = client.delete(
            f"/v1.0/process-models/{test_process_group_id}/{test_process_model_id}",
            headers=self.logged_in_headers(with_super_admin_user),
        )

        # make sure we get an error in the response
        assert response.status_code == 400
        data = json.loads(response.get_data(as_text=True))
        assert data["error_code"] == "existing_instances"
        assert (
            data["message"]
            == "We cannot delete the model `sample`, there are existing instances that depend on it."
        )

    def test_process_model_update(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_process_model_update."""
        self.create_process_model_with_api(
            client,
            user=with_super_admin_user,
        )
        process_model = ProcessModelService().get_process_model("make_cookies")
        assert process_model.id == "make_cookies"
        assert process_model.display_name == "Cooooookies"
        assert process_model.is_review is False
        assert process_model.primary_file_name is None
        assert process_model.primary_process_id is None

        process_model.display_name = "Updated Display Name"
        process_model.primary_file_name = "superduper.bpmn"
        process_model.primary_process_id = "superduper"
        process_model.is_review = True  # not in the include list, so get ignored

        response = client.put(
            f"/v1.0/process-models/{process_model.process_group_id}/{process_model.id}",
            headers=self.logged_in_headers(with_super_admin_user),
            content_type="application/json",
            data=json.dumps(ProcessModelInfoSchema().dump(process_model)),
        )
        assert response.status_code == 200
        assert response.json is not None
        assert response.json["display_name"] == "Updated Display Name"
        assert response.json["primary_file_name"] == "superduper.bpmn"
        assert response.json["primary_process_id"] == "superduper"
        assert response.json["is_review"] is False

    def test_process_model_list(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_process_model_list."""
        # create a group
        group_id = "test_group"
        self.create_process_group(client, with_super_admin_user, group_id)

        # add 5 models to the group
        for i in range(5):
            process_model_identifier = f"test_model_{i}"
            model_display_name = f"Test Model {i}"
            model_description = f"Test Model {i} Description"
            self.create_process_model_with_api(
                client,
                process_group_id=group_id,
                process_model_id=process_model_identifier,
                process_model_display_name=model_display_name,
                process_model_description=model_description,
                user=with_super_admin_user,
            )

        # get all models
        response = client.get(
            f"/v1.0/process-models?process_group_identifier={group_id}",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.json is not None
        assert len(response.json["results"]) == 5
        assert response.json["pagination"]["count"] == 5
        assert response.json["pagination"]["total"] == 5
        assert response.json["pagination"]["pages"] == 1

        # get first page, 1 per page
        response = client.get(
            f"/v1.0/process-models?page=1&per_page=1&process_group_identifier={group_id}",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.json is not None
        assert len(response.json["results"]) == 1
        assert response.json["results"][0]["id"] == "test_model_0"
        assert response.json["pagination"]["count"] == 1
        assert response.json["pagination"]["total"] == 5
        assert response.json["pagination"]["pages"] == 5

        # get second page, 1 per page
        response = client.get(
            f"/v1.0/process-models?page=2&per_page=1&process_group_identifier={group_id}",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.json is not None
        assert len(response.json["results"]) == 1
        assert response.json["results"][0]["id"] == "test_model_1"
        assert response.json["pagination"]["count"] == 1
        assert response.json["pagination"]["total"] == 5
        assert response.json["pagination"]["pages"] == 5

        # get first page, 3 per page
        response = client.get(
            f"/v1.0/process-models?page=1&per_page=3&process_group_identifier={group_id}",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.json is not None
        assert len(response.json["results"]) == 3
        assert response.json["results"][0]["id"] == "test_model_0"
        assert response.json["pagination"]["count"] == 3
        assert response.json["pagination"]["total"] == 5
        assert response.json["pagination"]["pages"] == 2

        # get second page, 3 per page
        response = client.get(
            f"/v1.0/process-models?page=2&per_page=3&process_group_identifier={group_id}",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        # there should only be 2 left
        assert response.json is not None
        assert len(response.json["results"]) == 2
        assert response.json["results"][0]["id"] == "test_model_3"
        assert response.json["pagination"]["count"] == 2
        assert response.json["pagination"]["total"] == 5
        assert response.json["pagination"]["pages"] == 2

    def test_process_group_add(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_add_process_group."""
        process_group = ProcessGroup(
            id="test",
            display_name="Another Test Category",
            display_order=0,
            admin=False,
        )
        response = client.post(
            "/v1.0/process-groups",
            headers=self.logged_in_headers(with_super_admin_user),
            content_type="application/json",
            data=json.dumps(ProcessGroupSchema().dump(process_group)),
        )
        assert response.status_code == 201

        # Check what is returned
        result = ProcessGroupSchema().loads(response.get_data(as_text=True))
        assert result is not None
        assert result.display_name == "Another Test Category"
        assert result.id == "test"

        # Check what is persisted
        persisted = ProcessModelService().get_process_group("test")
        assert persisted.display_name == "Another Test Category"
        assert persisted.id == "test"

    def test_process_group_delete(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_process_group_delete."""
        process_group_id = "test"
        process_group_display_name = "My Process Group"

        self.create_process_group(
            client,
            with_super_admin_user,
            process_group_id,
            display_name=process_group_display_name,
        )
        persisted = ProcessModelService().get_process_group(process_group_id)
        assert persisted is not None
        assert persisted.id == process_group_id

        client.delete(
            f"/v1.0/process-groups/{process_group_id}",
            headers=self.logged_in_headers(with_super_admin_user),
        )

        with pytest.raises(ProcessEntityNotFoundError):
            ProcessModelService().get_process_group(process_group_id)

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

        self.create_process_group(
            client, with_super_admin_user, group_id, display_name=group_display_name
        )
        process_group = ProcessModelService().get_process_group(group_id)

        assert process_group.display_name == group_display_name

        process_group.display_name = "Modified Display Name"

        response = client.put(
            f"/v1.0/process-groups/{group_id}",
            headers=self.logged_in_headers(with_super_admin_user),
            content_type="application/json",
            data=json.dumps(ProcessGroupSchema().dump(process_group)),
        )
        assert response.status_code == 200

        process_group = ProcessModelService().get_process_group(group_id)
        assert process_group.display_name == "Modified Display Name"

    def test_process_group_list(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_process_group_list."""
        # add 5 groups
        for i in range(5):
            group_id = f"test_process_group_{i}"
            group_display_name = f"Test Group {i}"
            self.create_process_group(
                client, with_super_admin_user, group_id, display_name=group_display_name
            )

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

    def test_process_model_file_update_fails_if_no_file_given(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_process_model_file_update."""
        self.create_spec_file(client, user=with_super_admin_user)

        process_model = load_test_spec("random_fact")
        data = {"key1": "THIS DATA"}
        response = client.put(
            f"/v1.0/process-models/{process_model.process_group_id}/{process_model.id}/files/random_fact.svg",
            data=data,
            follow_redirects=True,
            content_type="multipart/form-data",
            headers=self.logged_in_headers(with_super_admin_user),
        )

        assert response.status_code == 400
        assert response.json is not None
        assert response.json["error_code"] == "no_file_given"

    def test_process_model_file_update_fails_if_contents_is_empty(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_process_model_file_update."""
        self.create_spec_file(client, user=with_super_admin_user)

        process_model = load_test_spec("random_fact")
        data = {"file": (io.BytesIO(b""), "random_fact.svg")}
        response = client.put(
            f"/v1.0/process-models/{process_model.process_group_id}/{process_model.id}/files/random_fact.svg",
            data=data,
            follow_redirects=True,
            content_type="multipart/form-data",
            headers=self.logged_in_headers(with_super_admin_user),
        )

        assert response.status_code == 400
        assert response.json is not None
        assert response.json["error_code"] == "file_contents_empty"

    def test_process_model_file_update(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_process_model_file_update."""
        original_file = self.create_spec_file(client, user=with_super_admin_user)

        process_model = load_test_spec("random_fact")
        new_file_contents = b"THIS_IS_NEW_DATA"
        data = {"file": (io.BytesIO(new_file_contents), "random_fact.svg")}
        response = client.put(
            f"/v1.0/process-models/{process_model.process_group_id}/{process_model.id}/files/random_fact.svg",
            data=data,
            follow_redirects=True,
            content_type="multipart/form-data",
            headers=self.logged_in_headers(with_super_admin_user),
        )

        assert response.status_code == 200
        assert response.json is not None
        assert response.json["ok"]

        response = client.get(
            f"/v1.0/process-models/{process_model.process_group_id}/{process_model.id}/files/random_fact.svg",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200
        updated_file = json.loads(response.get_data(as_text=True))
        assert original_file != updated_file
        assert updated_file["file_contents"] == new_file_contents.decode()

    def test_process_model_file_delete_when_bad_process_model(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_process_model_file_update."""
        self.create_spec_file(client, user=with_super_admin_user)

        process_model = load_test_spec("random_fact")
        response = client.delete(
            f"/v1.0/process-models/INCORRECT-NON-EXISTENT-GROUP/{process_model.id}/files/random_fact.svg",
            follow_redirects=True,
            headers=self.logged_in_headers(with_super_admin_user),
        )

        assert response.status_code == 400
        assert response.json is not None
        assert response.json["error_code"] == "process_model_cannot_be_found"

    def test_process_model_file_delete_when_bad_file(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_process_model_file_update."""
        self.create_spec_file(client, user=with_super_admin_user)

        process_model = load_test_spec("random_fact")
        response = client.delete(
            f"/v1.0/process-models/{process_model.process_group_id}/{process_model.id}/files/random_fact_DOES_NOT_EXIST.svg",
            follow_redirects=True,
            headers=self.logged_in_headers(with_super_admin_user),
        )

        assert response.status_code == 400
        assert response.json is not None
        assert response.json["error_code"] == "process_model_file_cannot_be_found"

    def test_process_model_file_delete(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_process_model_file_update."""
        self.create_spec_file(client, user=with_super_admin_user)

        process_model = load_test_spec("random_fact")
        response = client.delete(
            f"/v1.0/process-models/{process_model.process_group_id}/{process_model.id}/files/random_fact.svg",
            follow_redirects=True,
            headers=self.logged_in_headers(with_super_admin_user),
        )

        assert response.status_code == 200
        assert response.json is not None
        assert response.json["ok"]

        response = client.get(
            f"/v1.0/process-models/{process_model.process_group_id}/{process_model.id}/files/random_fact.svg",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 404

    def test_get_file(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_get_file."""
        test_process_group_id = "group_id1"
        process_model_dir_name = "hello_world"
        load_test_spec(process_model_dir_name, process_group_id=test_process_group_id)
        response = client.get(
            f"/v1.0/process-models/{test_process_group_id}/{process_model_dir_name}/files/hello_world.bpmn",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200
        assert response.json is not None
        assert response.json["name"] == "hello_world.bpmn"
        assert response.json["process_group_id"] == "group_id1"
        assert response.json["process_model_id"] == "hello_world"

    def test_get_workflow_from_workflow_spec(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_get_workflow_from_workflow_spec."""
        process_model = load_test_spec("hello_world")
        response = client.post(
            f"/v1.0/process-models/{process_model.process_group_id}/{process_model.id}/process-instances",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 201
        assert response.json is not None
        assert "hello_world" == response.json["process_model_identifier"]
        # assert('Task_GetName' == response.json['next_task']['name'])

    def test_get_process_groups_when_none(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_get_process_groups_when_none."""
        response = client.get(
            "/v1.0/process-groups",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200
        assert response.json is not None
        assert response.json["results"] == []

    def test_get_process_groups_when_there_are_some(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_get_process_groups_when_there_are_some."""
        load_test_spec("hello_world")
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

    def test_get_process_group_when_found(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_get_process_group_when_found."""
        test_process_group_id = "group_id1"
        process_model_dir_name = "hello_world"
        load_test_spec(process_model_dir_name, process_group_id=test_process_group_id)
        response = client.get(
            f"/v1.0/process-groups/{test_process_group_id}",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200
        assert response.json is not None
        assert response.json["id"] == test_process_group_id
        assert response.json["process_models"][0]["id"] == process_model_dir_name

    def test_get_process_model_when_found(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_get_process_model_when_found."""
        test_process_group_id = "group_id1"
        process_model_dir_name = "hello_world"
        load_test_spec(process_model_dir_name, process_group_id=test_process_group_id)
        response = client.get(
            f"/v1.0/process-models/{test_process_group_id}/{process_model_dir_name}",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200
        assert response.json is not None
        assert response.json["id"] == process_model_dir_name
        assert len(response.json["files"]) == 1
        assert response.json["files"][0]["name"] == "hello_world.bpmn"

    def test_get_process_model_when_not_found(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_get_process_model_when_not_found."""
        process_model_dir_name = "THIS_NO_EXISTS"
        group_id = self.create_process_group(client, with_super_admin_user, "my_group")
        response = client.get(
            f"/v1.0/process-models/{group_id}/{process_model_dir_name}",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 400
        assert response.json is not None
        assert response.json["error_code"] == "process_model_cannot_be_found"

    def test_process_instance_create(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_process_instance_create."""
        test_process_group_id = "runs_without_input"
        test_process_model_id = "sample"
        headers = self.logged_in_headers(with_super_admin_user)
        response = self.create_process_instance(
            client, test_process_group_id, test_process_model_id, headers
        )
        assert response.json is not None
        assert response.json["updated_at_in_seconds"] is not None
        assert response.json["status"] == "not_started"
        assert response.json["process_model_identifier"] == test_process_model_id
        # TODO: mock out the responses for the git service so we can do something like this
        # current_revision = GitService.get_current_revision()
        # assert response.json["bpmn_version_control_identifier"] == current_revision

    def test_process_instance_run(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_process_instance_run."""
        process_group_id = "runs_without_input"
        process_model_id = "sample"
        headers = self.logged_in_headers(with_super_admin_user)
        response = self.create_process_instance(
            client, process_group_id, process_model_id, headers
        )
        assert response.json is not None
        process_instance_id = response.json["id"]
        response = client.post(
            f"/v1.0/process-models/{process_group_id}/{process_model_id}/process-instances/{process_instance_id}/run",
            headers=self.logged_in_headers(with_super_admin_user),
        )

        assert response.json is not None
        assert type(response.json["updated_at_in_seconds"]) is int
        assert response.json["updated_at_in_seconds"] > 0
        assert response.json["status"] == "complete"
        assert response.json["process_model_identifier"] == process_model_id
        assert (
            response.json["data"]["current_user"]["username"]
            == with_super_admin_user.username
        )
        assert response.json["data"]["Mike"] == "Awesome"
        assert response.json["data"]["person"] == "Kevin"

    def test_process_instance_show(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_process_instance_show."""
        process_group_id = "simple_script"
        process_model_id = "simple_script"
        headers = self.logged_in_headers(with_super_admin_user)
        create_response = self.create_process_instance(
            client, process_group_id, process_model_id, headers
        )
        assert create_response.json is not None
        process_instance_id = create_response.json["id"]
        client.post(
            f"/v1.0/process-models/{process_group_id}/{process_model_id}/process-instances/{process_instance_id}/run",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        show_response = client.get(
            f"/v1.0/process-models/{process_group_id}/{process_model_id}/process-instances/{process_instance_id}",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert show_response.json is not None
        file_system_root = FileSystemService.root_path()
        file_path = f"{file_system_root}/{process_group_id}/{process_model_id}/{process_model_id}.bpmn"
        with open(file_path) as f_open:
            xml_file_contents = f_open.read()
            assert show_response.json["bpmn_xml_file_contents"] == xml_file_contents

    def test_message_start_when_starting_process_instance(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_message_start_when_starting_process_instance."""
        # ensure process model is loaded in db
        load_test_spec(
            "message_receiver",
            process_model_source_directory="message_send_one_conversation",
            bpmn_file_name="message_receiver",
        )
        message_model_identifier = "message_send"
        payload = {
            "topica": "the_topica_string",
            "topicb": "the_topicb_string",
            "andThis": "another_item_non_key",
        }
        response = client.post(
            f"/v1.0/messages/{message_model_identifier}",
            content_type="application/json",
            headers=self.logged_in_headers(with_super_admin_user),
            data=json.dumps({"payload": payload}),
        )
        assert response.status_code == 200
        json_data = response.json
        assert json_data
        assert json_data["status"] == "complete"
        process_instance_id = json_data["id"]
        process_instance = ProcessInstanceModel.query.filter_by(
            id=process_instance_id
        ).first()
        assert process_instance

        processor = ProcessInstanceProcessor(process_instance)
        process_instance_data = processor.get_data()
        assert process_instance_data
        assert process_instance_data["the_payload"] == payload

    def test_message_start_when_providing_message_to_running_process_instance(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_message_start_when_providing_message_to_running_process_instance."""
        process_model = load_test_spec(
            "message_sender",
            process_model_source_directory="message_send_one_conversation",
            bpmn_file_name="message_sender",
        )
        message_model_identifier = "message_response"
        payload = {
            "the_payload": {
                "topica": "the_payload.topica_string",
                "topicb": "the_payload.topicb_string",
                "andThis": "another_item_non_key",
            }
        }
        response = self.create_process_instance(
            client,
            process_model.process_group_id,
            process_model.id,
            self.logged_in_headers(with_super_admin_user),
        )
        assert response.json is not None
        process_instance_id = response.json["id"]

        response = client.post(
            f"/v1.0/process-models/{process_model.process_group_id}/"
            f"{process_model.id}/process-instances/{process_instance_id}/run",
            headers=self.logged_in_headers(with_super_admin_user),
        )

        assert response.json is not None

        response = client.post(
            f"/v1.0/messages/{message_model_identifier}",
            content_type="application/json",
            headers=self.logged_in_headers(with_super_admin_user),
            data=json.dumps(
                {"payload": payload, "process_instance_id": process_instance_id}
            ),
        )
        assert response.status_code == 200
        json_data = response.json
        assert json_data
        assert json_data["status"] == "complete"
        process_instance_id = json_data["id"]
        process_instance = ProcessInstanceModel.query.filter_by(
            id=process_instance_id
        ).first()
        assert process_instance

        processor = ProcessInstanceProcessor(process_instance)
        process_instance_data = processor.get_data()
        assert process_instance_data
        assert process_instance_data["the_payload"] == payload

    def test_process_instance_can_be_terminated(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_message_start_when_providing_message_to_running_process_instance."""
        # this task will wait on a catch event
        process_model = load_test_spec(
            "message_sender",
            process_model_source_directory="message_send_one_conversation",
            bpmn_file_name="message_sender",
        )
        response = self.create_process_instance(
            client,
            process_model.process_group_id,
            process_model.id,
            self.logged_in_headers(with_super_admin_user),
        )
        assert response.json is not None
        process_instance_id = response.json["id"]

        response = client.post(
            f"/v1.0/process-models/{process_model.process_group_id}/"
            f"{process_model.id}/process-instances/{process_instance_id}/run",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200
        assert response.json is not None

        response = client.post(
            f"/v1.0/process-models/{process_model.process_group_id}/"
            f"{process_model.id}/process-instances/{process_instance_id}/terminate",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200
        assert response.json is not None

        process_instance = ProcessInstanceModel.query.filter_by(
            id=process_instance_id
        ).first()
        assert process_instance
        assert process_instance.status == "terminated"

    def test_process_instance_delete(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_process_instance_delete."""
        process_group_id = "my_process_group"
        process_model_id = "user_task"

        headers = self.logged_in_headers(with_super_admin_user)
        response = self.create_process_instance(
            client, process_group_id, process_model_id, headers
        )
        assert response.json is not None
        process_instance_id = response.json["id"]

        response = client.post(
            f"/v1.0/process-models/{process_group_id}/{process_model_id}/process-instances/{process_instance_id}/run",
            headers=self.logged_in_headers(with_super_admin_user),
        )

        assert response.json is not None
        task_events = (
            db.session.query(TaskEventModel)
            .filter(TaskEventModel.process_instance_id == process_instance_id)
            .all()
        )
        assert len(task_events) == 1
        task_event = task_events[0]
        assert task_event.user_id == with_super_admin_user.id

        delete_response = client.delete(
            f"/v1.0/process-models/{process_group_id}/{process_model_id}/process-instances/{process_instance_id}",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert delete_response.status_code == 200

    def test_process_instance_run_user_task_creates_task_event(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_process_instance_run_user_task."""
        process_group_id = "my_process_group"
        process_model_id = "user_task"

        headers = self.logged_in_headers(with_super_admin_user)
        response = self.create_process_instance(
            client, process_group_id, process_model_id, headers
        )
        assert response.json is not None
        process_instance_id = response.json["id"]

        response = client.post(
            f"/v1.0/process-models/{process_group_id}/{process_model_id}/process-instances/{process_instance_id}/run",
            headers=self.logged_in_headers(with_super_admin_user),
        )

        assert response.json is not None
        task_events = (
            db.session.query(TaskEventModel)
            .filter(TaskEventModel.process_instance_id == process_instance_id)
            .all()
        )
        assert len(task_events) == 1
        task_event = task_events[0]
        assert task_event.user_id == with_super_admin_user.id
        # TODO: When user tasks work, we need to add some more assertions for action, task_state, etc.

    def test_task_show(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_process_instance_run_user_task."""
        process_group_id = "my_process_group"
        process_model_id = "dynamic_enum_select_fields"

        headers = self.logged_in_headers(with_super_admin_user)
        response = self.create_process_instance(
            client, process_group_id, process_model_id, headers
        )
        assert response.json is not None
        process_instance_id = response.json["id"]

        response = client.post(
            f"/v1.0/process-models/{process_group_id}/{process_model_id}/process-instances/{process_instance_id}/run",
            headers=self.logged_in_headers(with_super_admin_user),
        )

        assert response.json is not None
        active_tasks = (
            db.session.query(ActiveTaskModel)
            .filter(ActiveTaskModel.process_instance_id == process_instance_id)
            .all()
        )
        assert len(active_tasks) == 1
        active_task = active_tasks[0]
        response = client.get(
            f"/v1.0/tasks/{process_instance_id}/{active_task.task_id}",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.json is not None
        assert (
            response.json["form_schema"]["definitions"]["Color"]["anyOf"][1]["title"]
            == "Green"
        )

    def test_process_instance_list_with_default_list(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_process_instance_list_with_default_list."""
        test_process_group_id = "runs_without_input"
        process_model_dir_name = "sample"
        headers = self.logged_in_headers(with_super_admin_user)
        self.create_process_instance(
            client, test_process_group_id, process_model_dir_name, headers
        )

        response = client.get(
            "/v1.0/process-instances",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200
        assert response.json is not None
        assert len(response.json["results"]) == 1
        assert response.json["pagination"]["count"] == 1
        assert response.json["pagination"]["pages"] == 1
        assert response.json["pagination"]["total"] == 1

        process_instance_dict = response.json["results"][0]
        assert type(process_instance_dict["id"]) is int
        assert (
            process_instance_dict["process_model_identifier"] == process_model_dir_name
        )
        assert (
            process_instance_dict["process_group_identifier"] == test_process_group_id
        )
        assert type(process_instance_dict["start_in_seconds"]) is int
        assert process_instance_dict["start_in_seconds"] > 0
        assert process_instance_dict["end_in_seconds"] is None
        assert process_instance_dict["status"] == "not_started"

    def test_process_instance_list_with_paginated_items(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_process_instance_list_with_paginated_items."""
        test_process_group_id = "runs_without_input"
        process_model_dir_name = "sample"
        headers = self.logged_in_headers(with_super_admin_user)
        self.create_process_instance(
            client, test_process_group_id, process_model_dir_name, headers
        )
        self.create_process_instance(
            client, test_process_group_id, process_model_dir_name, headers
        )
        self.create_process_instance(
            client, test_process_group_id, process_model_dir_name, headers
        )
        self.create_process_instance(
            client, test_process_group_id, process_model_dir_name, headers
        )
        self.create_process_instance(
            client, test_process_group_id, process_model_dir_name, headers
        )

        response = client.get(
            "/v1.0/process-instances?per_page=2&page=3",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200
        assert response.json is not None
        assert len(response.json["results"]) == 1
        assert response.json["pagination"]["count"] == 1
        assert response.json["pagination"]["pages"] == 3
        assert response.json["pagination"]["total"] == 5

        response = client.get(
            "/v1.0/process-instances?per_page=2&page=1",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200
        assert response.json is not None
        assert len(response.json["results"]) == 2
        assert response.json["pagination"]["count"] == 2
        assert response.json["pagination"]["pages"] == 3
        assert response.json["pagination"]["total"] == 5

    def test_process_instance_list_filter(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_process_instance_list_filter."""
        test_process_group_id = "runs_without_input"
        test_process_model_id = "sample"
        load_test_spec(test_process_model_id, process_group_id=test_process_group_id)

        statuses = [status.value for status in ProcessInstanceStatus]
        # create 5 instances with different status, and different start_in_seconds/end_in_seconds
        for i in range(5):
            process_instance = ProcessInstanceModel(
                status=ProcessInstanceStatus[statuses[i]].value,
                process_initiator=with_super_admin_user,
                process_model_identifier=test_process_model_id,
                process_group_identifier=test_process_group_id,
                updated_at_in_seconds=round(time.time()),
                start_in_seconds=(1000 * i) + 1000,
                end_in_seconds=(1000 * i) + 2000,
                bpmn_json=json.dumps({"i": i}),
            )
            db.session.add(process_instance)
        db.session.commit()

        # Without filtering we should get all 5 instances
        response = client.get(
            f"/v1.0/process-instances?process_group_identifier={test_process_group_id}&process_model_identifier={test_process_model_id}",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.json is not None
        results = response.json["results"]
        assert len(results) == 5

        # filter for each of the status
        # we should get 1 instance each time
        for i in range(5):
            response = client.get(
                f"/v1.0/process-instances?process_status={ProcessInstanceStatus[statuses[i]].value}&process_group_identifier={test_process_group_id}&process_model_identifier={test_process_model_id}",
                headers=self.logged_in_headers(with_super_admin_user),
            )
            assert response.json is not None
            results = response.json["results"]
            assert len(results) == 1
            assert results[0]["status"] == ProcessInstanceStatus[statuses[i]].value

        response = client.get(
            f"/v1.0/process-instances?process_status=not_started,complete&process_group_identifier={test_process_group_id}&process_model_identifier={test_process_model_id}",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.json is not None
        results = response.json["results"]
        assert len(results) == 2
        assert results[0]["status"] in ["complete", "not_started"]
        assert results[1]["status"] in ["complete", "not_started"]

        # filter by start/end seconds
        # start > 1000 - this should eliminate the first
        response = client.get(
            "/v1.0/process-instances?start_from=1001",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.json is not None
        results = response.json["results"]
        assert len(results) == 4
        for i in range(4):
            assert json.loads(results[i]["bpmn_json"])["i"] in (1, 2, 3, 4)

        # start > 2000, end < 5000 - this should eliminate the first 2 and the last
        response = client.get(
            "/v1.0/process-instances?start_from=2001&end_till=5999",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.json is not None
        results = response.json["results"]
        assert len(results) == 2
        assert json.loads(results[0]["bpmn_json"])["i"] in (2, 3)
        assert json.loads(results[1]["bpmn_json"])["i"] in (2, 3)

        # start > 1000, start < 4000 - this should eliminate the first and the last 2
        response = client.get(
            "/v1.0/process-instances?start_from=1001&start_till=3999",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.json is not None
        results = response.json["results"]
        assert len(results) == 2
        assert json.loads(results[0]["bpmn_json"])["i"] in (1, 2)
        assert json.loads(results[1]["bpmn_json"])["i"] in (1, 2)

        # end > 2000, end < 6000 - this should eliminate the first and the last
        response = client.get(
            "/v1.0/process-instances?end_from=2001&end_till=5999",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.json is not None
        results = response.json["results"]
        assert len(results) == 3
        for i in range(3):
            assert json.loads(results[i]["bpmn_json"])["i"] in (1, 2, 3)

    def test_process_instance_report_list(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_process_instance_report_list."""
        process_group_identifier = "runs_without_input"
        process_model_identifier = "sample"
        self.logged_in_headers(with_super_admin_user)
        load_test_spec(
            process_model_identifier, process_group_id=process_group_identifier
        )
        report_identifier = "testreport"
        report_metadata = {"order_by": ["month"]}
        ProcessInstanceReportModel.create_with_attributes(
            identifier=report_identifier,
            process_group_identifier=process_group_identifier,
            process_model_identifier=process_model_identifier,
            report_metadata=report_metadata,
            user=with_super_admin_user,
        )
        response = client.get(
            f"/v1.0/process-models/{process_group_identifier}/{process_model_identifier}/process-instances/reports",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200
        assert response.json is not None
        assert len(response.json) == 1
        assert response.json[0]["identifier"] == report_identifier
        assert response.json[0]["report_metadata"]["order_by"] == ["month"]

    def test_process_instance_report_show_with_default_list(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
        setup_process_instances_for_reports: list[ProcessInstanceModel],
    ) -> None:
        """Test_process_instance_report_show_with_default_list."""
        test_process_group_id = "runs_without_input"
        process_model_dir_name = "sample"

        report_metadata = {
            "columns": [
                {"Header": "id", "accessor": "id"},
                {
                    "Header": "process_model_identifier",
                    "accessor": "process_model_identifier",
                },
                {"Header": "process_group_id", "accessor": "process_group_identifier"},
                {"Header": "start_in_seconds", "accessor": "start_in_seconds"},
                {"Header": "status", "accessor": "status"},
                {"Header": "Name", "accessor": "name"},
                {"Header": "Status", "accessor": "status"},
            ],
            "order_by": ["test_score"],
            "filter_by": [
                {"field_name": "grade_level", "operator": "equals", "field_value": 2}
            ],
        }

        ProcessInstanceReportModel.create_with_attributes(
            identifier="sure",
            process_group_identifier=test_process_group_id,
            process_model_identifier=process_model_dir_name,
            report_metadata=report_metadata,
            user=with_super_admin_user,
        )

        response = client.get(
            f"/v1.0/process-models/{test_process_group_id}/{process_model_dir_name}/process-instances/reports/sure",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200
        assert response.json is not None
        assert len(response.json["results"]) == 2
        assert response.json["pagination"]["count"] == 2
        assert response.json["pagination"]["pages"] == 1
        assert response.json["pagination"]["total"] == 2

        process_instance_dict = response.json["results"][0]
        assert type(process_instance_dict["id"]) is int
        assert (
            process_instance_dict["process_model_identifier"] == process_model_dir_name
        )
        assert (
            process_instance_dict["process_group_identifier"] == test_process_group_id
        )
        assert type(process_instance_dict["start_in_seconds"]) is int
        assert process_instance_dict["start_in_seconds"] > 0
        assert process_instance_dict["status"] == "complete"

    def test_process_instance_report_show_with_dynamic_filter_and_query_param(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
        setup_process_instances_for_reports: list[ProcessInstanceModel],
    ) -> None:
        """Test_process_instance_report_show_with_default_list."""
        test_process_group_id = "runs_without_input"
        process_model_dir_name = "sample"

        report_metadata = {
            "filter_by": [
                {
                    "field_name": "grade_level",
                    "operator": "equals",
                    "field_value": "{{grade_level}}",
                }
            ],
        }

        ProcessInstanceReportModel.create_with_attributes(
            identifier="sure",
            process_group_identifier=test_process_group_id,
            process_model_identifier=process_model_dir_name,
            report_metadata=report_metadata,
            user=with_super_admin_user,
        )

        response = client.get(
            f"/v1.0/process-models/{test_process_group_id}/{process_model_dir_name}/process-instances/reports/sure?grade_level=1",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200
        assert response.json is not None
        assert len(response.json["results"]) == 1

    def test_process_instance_report_show_with_bad_identifier(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
        setup_process_instances_for_reports: list[ProcessInstanceModel],
    ) -> None:
        """Test_process_instance_report_show_with_default_list."""
        test_process_group_id = "runs_without_input"
        process_model_dir_name = "sample"

        response = client.get(
            f"/v1.0/process-models/{test_process_group_id}/{process_model_dir_name}/process-instances/reports/sure?grade_level=1",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 404
        data = json.loads(response.get_data(as_text=True))
        assert data["error_code"] == "unknown_process_instance_report"

    def setup_testing_instance(
        self,
        client: FlaskClient,
        process_group_id: str,
        process_model_id: str,
        with_super_admin_user: UserModel,
    ) -> Any:
        """Setup_testing_instance."""
        headers = self.logged_in_headers(with_super_admin_user)
        response = self.create_process_instance(
            client, process_group_id, process_model_id, headers
        )
        process_instance = response.json
        assert isinstance(process_instance, dict)
        process_instance_id = process_instance["id"]
        return process_instance_id

    def test_error_handler(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_error_handler."""
        process_group_id = "data"
        process_model_id = "error"

        process_instance_id = self.setup_testing_instance(
            client, process_group_id, process_model_id, with_super_admin_user
        )

        process = (
            db.session.query(ProcessInstanceModel)
            .filter(ProcessInstanceModel.id == process_instance_id)
            .first()
        )
        assert process is not None
        assert process.status == "not_started"

        response = client.post(
            f"/v1.0/process-models/{process_group_id}/{process_model_id}/process-instances/{process_instance_id}/run",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 400

        api_error = json.loads(response.get_data(as_text=True))
        assert api_error["error_code"] == "task_error"
        assert (
            'TypeError:can only concatenate str (not "int") to str'
            in api_error["message"]
        )

        process = (
            db.session.query(ProcessInstanceModel)
            .filter(ProcessInstanceModel.id == process_instance_id)
            .first()
        )
        assert process is not None
        assert process.status == "faulted"

    def test_error_handler_suspend(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_error_handler_suspend."""
        process_group_id = "data"
        process_model_id = "error"

        process_instance_id = self.setup_testing_instance(
            client, process_group_id, process_model_id, with_super_admin_user
        )
        process_model = ProcessModelService().get_process_model(
            process_model_id, process_group_id
        )
        ProcessModelService().update_spec(
            process_model,
            {"fault_or_suspend_on_exception": NotificationType.suspend.value},
        )

        process = (
            db.session.query(ProcessInstanceModel)
            .filter(ProcessInstanceModel.id == process_instance_id)
            .first()
        )
        assert process is not None
        assert process.status == "not_started"

        response = client.post(
            f"/v1.0/process-models/{process_group_id}/{process_model_id}/process-instances/{process_instance_id}/run",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 400

        process = (
            db.session.query(ProcessInstanceModel)
            .filter(ProcessInstanceModel.id == process_instance_id)
            .first()
        )
        assert process is not None
        assert process.status == "suspended"

    def test_error_handler_with_email(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_error_handler."""
        process_group_id = "data"
        process_model_id = "error"

        process_instance_id = self.setup_testing_instance(
            client, process_group_id, process_model_id, with_super_admin_user
        )

        process_model = ProcessModelService().get_process_model(
            process_model_id, process_group_id
        )
        ProcessModelService().update_spec(
            process_model,
            {"exception_notification_addresses": ["with_super_admin_user@example.com"]},
        )

        mail = app.config["MAIL_APP"]
        with mail.record_messages() as outbox:

            response = client.post(
                f"/v1.0/process-models/{process_group_id}/{process_model_id}/process-instances/{process_instance_id}/run",
                headers=self.logged_in_headers(with_super_admin_user),
            )
            assert response.status_code == 400
            assert len(outbox) == 1
            message = outbox[0]
            assert message.subject == "Unexpected error in app"
            assert (
                message.body == 'TypeError:can only concatenate str (not "int") to str'
            )
            assert message.recipients == process_model.exception_notification_addresses

        process = (
            db.session.query(ProcessInstanceModel)
            .filter(ProcessInstanceModel.id == process_instance_id)
            .first()
        )
        assert process is not None
        assert process.status == "faulted"

    def test_process_model_file_create(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_process_model_file_create."""
        process_group_id = "hello_world"
        process_model_id = "hello_world"
        file_name = "hello_world.svg"
        file_data = b"abc123"

        result = self.create_spec_file(
            client,
            process_group_id=process_group_id,
            process_model_id=process_model_id,
            file_name=file_name,
            file_data=file_data,
            user=with_super_admin_user,
        )
        assert result["process_group_id"] == process_group_id
        assert result["process_model_id"] == process_model_id
        assert result["name"] == file_name
        assert bytes(str(result["file_contents"]), "utf-8") == file_data

    def test_can_get_message_instances_by_process_instance_id_and_without(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_can_get_message_instances_by_process_instance_id."""
        load_test_spec(
            "message_receiver",
            process_model_source_directory="message_send_one_conversation",
            bpmn_file_name="message_receiver",
        )
        message_model_identifier = "message_send"
        payload = {
            "topica": "the_topica_string",
            "topicb": "the_topicb_string",
            "andThis": "another_item_non_key",
        }
        response = client.post(
            f"/v1.0/messages/{message_model_identifier}",
            content_type="application/json",
            headers=self.logged_in_headers(with_super_admin_user),
            data=json.dumps({"payload": payload}),
        )
        assert response.status_code == 200
        assert response.json is not None
        process_instance_id_one = response.json["id"]

        response = client.post(
            f"/v1.0/messages/{message_model_identifier}",
            content_type="application/json",
            headers=self.logged_in_headers(with_super_admin_user),
            data=json.dumps({"payload": payload}),
        )
        assert response.status_code == 200
        assert response.json is not None
        process_instance_id_two = response.json["id"]

        response = client.get(
            f"/v1.0/messages?process_instance_id={process_instance_id_one}",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200
        assert response.json is not None
        assert len(response.json["results"]) == 1
        assert (
            response.json["results"][0]["process_instance_id"]
            == process_instance_id_one
        )

        response = client.get(
            f"/v1.0/messages?process_instance_id={process_instance_id_two}",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200
        assert response.json is not None
        assert len(response.json["results"]) == 1
        assert (
            response.json["results"][0]["process_instance_id"]
            == process_instance_id_two
        )

        response = client.get(
            "/v1.0/messages",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200
        assert response.json is not None
        assert len(response.json["results"]) == 2

    # TODO: test the auth callback endpoint
    # def test_can_store_authentication_secret(
    #     self, app: Flask, client: FlaskClient, with_db_and_bpmn_file_cleanup: None
    # ) -> None:
    #     """Test_can_store_authentication_secret."""
    #     response = client.get(
    #         "/v1.0/authentication_callback",
    #         headers=self.logged_in_headers(user),
    #     )

    # def test_get_process_model(self):
    #
    #     load_test_spec('random_fact')
    #     response = client.get('/v1.0/workflow-specification/random_fact', headers=self.logged_in_headers())
    #     assert_success(response)
    #     json_data = json.loads(response.get_data(as_text=True))
    #     api_spec = WorkflowSpecInfoSchema().load(json_data)
    #
    #     fs_spec = process_model_service.get_spec('random_fact')
    #     assert(WorkflowSpecInfoSchema().dump(fs_spec) == json_data)
    #

    # def test_waku_debug_info(self) -> None:
    #     """Test_waku_debug_info."""
    #     debug_info_method = "get_waku_v2_debug_v1_info"
    #
    #     headers = {"Content-Type": "application/json"}
    #
    #     rpc_json = {
    #         "jsonrpc": "2.0",
    #         "method": debug_info_method,
    #         "params": [],
    #         "id": "id",
    #     }
    #
    #     request_url = "http://localhost:8545"
    #     rpc_response = requests.post(request_url, headers=headers, json=rpc_json)
    #
    #     rpc_json_text: dict = json.loads(rpc_response.text)
    #     assert isinstance(rpc_json_text, dict)
    #     # assert 'jsonrpc' in rpc_json_text
    #     # assert rpc_json_text['jsonrpc'] == '2.0'
    #     assert "result" in rpc_json_text
    #     result = rpc_json_text["result"]
    #     assert isinstance(result, dict)
    #     assert "listenAddresses" in result
    #     assert "enrUri" in result
    #
    #     print("test_call_waku")
    #
    # def test_send_message(self) -> None:
    #     """Test_send_message."""
    #     relay_message_method = "post_waku_v2_relay_v1_message"
    #
    #     headers = {"Content-Type": "application/json"}
    #
    #     # class WakuMessage:
    #     #     payload: str
    #     #     contentTopic: str  # Optional
    #     #     # version: int  # Optional
    #     #     timestamp: int  # Optional
    #     payload = "This is my message"
    #     contentTopic = "myTestTopic"  # noqa: N806
    #     timestamp = time.time()
    #
    #     waku_relay_message = {
    #         "payload": payload,
    #         "contentTopic": contentTopic,
    #         "timestamp": timestamp,
    #     }
    #
    #     # ["", [{"contentTopic":"/waku/2/default-content/proto"}]]
    #     params = ["/waku/2/default-waku/proto", {"message": waku_relay_message}]
    #     rpc_json = {
    #         "jsonrpc": "2.0",
    #         "method": relay_message_method,
    #         "params": params,
    #         "id": 1,
    #     }
    #
    #     request_url = "http://localhost:8545"
    #     rpc_response = requests.post(request_url, headers=headers, json=rpc_json)
    #     assert rpc_response.status_code == 200
    #
    #     rpc_json_data: dict = json.loads(rpc_response.text)
    #     assert "error" in rpc_json_data
    #     assert "result" in rpc_json_data
    #     assert rpc_json_data["error"] is None
    #     assert rpc_json_data["result"] is True
    #
    #     print("test_send_message")
    #
    # def test_get_waku_messages(self) -> None:
    #     """Test_get_waku_messages."""
    #     method = "get_waku_v2_store_v1_messages"
    #     headers = {"Content-Type": "application/json"}
    #     params = [{"contentTopic": "/waku/2/default-content/proto"}]
    #
    #     rpc_json = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
    #     request_url = "http://localhost:8545"
    #     rpc_response = requests.post(request_url, headers=headers, json=rpc_json)
    #     assert rpc_response.status_code == 200
    #
    #     rpc_json_data: dict = json.loads(rpc_response.text)
    #     assert "error" in rpc_json_data
    #     assert rpc_json_data["error"] is None
    #     assert "result" in rpc_json_data
    #     assert isinstance(rpc_json_data["result"], dict)
    #     assert "messages" in rpc_json_data["result"]
    #     assert "pagingInfo" in rpc_json_data["result"]
    #
    #     print("get_waku_messages")
