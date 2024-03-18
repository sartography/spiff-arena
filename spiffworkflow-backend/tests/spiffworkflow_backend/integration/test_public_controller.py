import json
import re

from flask import Flask
from flask.testing import FlaskClient
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
from spiffworkflow_backend.models.task import TaskModel  # noqa: F401
from spiffworkflow_backend.services.authorization_service import AuthorizationService
from spiffworkflow_backend.services.authorization_service import GroupPermissionsDict

from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestPublicController(BaseTest):
    def test_can_get_a_form_from_message_start_event(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        group_info: list[GroupPermissionsDict] = [
            {
                "users": [],
                "name": app.config["SPIFFWORKFLOW_BACKEND_DEFAULT_PUBLIC_USER_GROUP"],
                "permissions": [{"actions": ["create", "read"], "uri": "/public/*"}],
            }
        ]
        AuthorizationService.refresh_permissions(group_info, group_permissions_only=True)
        process_model = load_test_spec(
            process_model_id="test_group/message-start-event-with-form",
            process_model_source_directory="message-start-event-with-form",
        )
        process_group_identifier, _ = process_model.modified_process_model_identifier().rsplit(":", 1)
        url = f"/v1.0/public/messages/form/{process_group_identifier}:bounty_start"

        response = client.get(url)
        assert response.status_code == 200
        assert response.json is not None
        assert "form" in response.json
        assert "confirmation_message_markdown" in response.json
        assert "task_guid" in response.json
        assert "form_schema" in response.json["form"]
        assert "form_ui_schema" in response.json["form"]
        assert response.json["form"]["form_schema"]["title"] == "Form for message start event"
        assert response.json["confirmation_message_markdown"] is None
        assert response.json["task_guid"] is None

    def test_can_submit_to_public_message_submit(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        group_info: list[GroupPermissionsDict] = [
            {
                "users": [],
                "name": app.config["SPIFFWORKFLOW_BACKEND_DEFAULT_PUBLIC_USER_GROUP"],
                "permissions": [{"actions": ["create", "read"], "uri": "/public/*"}],
            }
        ]
        AuthorizationService.refresh_permissions(group_info, group_permissions_only=True)
        process_model = load_test_spec(
            process_model_id="test_group/message-start-event-with-form",
            process_model_source_directory="message-start-event-with-form",
        )
        process_group_identifier, _ = process_model.modified_process_model_identifier().rsplit(":", 1)
        url = f"/v1.0/public/messages/submit/{process_group_identifier}:bounty_start?execution_mode=synchronous"

        response = client.post(
            url,
            data=json.dumps(
                {"firstName": "MyName"},
            ),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json is not None
        assert "form" in response.json
        assert "confirmation_message_markdown" in response.json
        assert "task_guid" in response.json
        assert response.json["form"] is None
        assert response.json["confirmation_message_markdown"] == "# Thanks\n\nWe hear you. Your name is **MyName**."
        assert response.json["task_guid"] is None

    def test_can_submit_to_public_message_submit_and_get_and_submit_subsequent_form(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        user = self.find_or_create_user("testuser1")
        admin_user = self.find_or_create_user("admin")
        headers = self.logged_in_headers(user, extra_token_payload={"public": True})
        group_info: list[GroupPermissionsDict] = [
            {
                "users": [user.username],
                "name": app.config["SPIFFWORKFLOW_BACKEND_DEFAULT_PUBLIC_USER_GROUP"],
                "permissions": [{"actions": ["create", "read", "update"], "uri": "/public/*"}],
            },
            {
                "users": [admin_user.username],
                "name": "admin",
                "permissions": [{"actions": ["all"], "uri": "/*"}],
            },
        ]
        AuthorizationService.refresh_permissions(group_info)
        process_model = load_test_spec(
            process_model_id="test_group/message-start-event-with-multiple-forms",
            process_model_source_directory="message-start-event-with-multiple-forms",
        )
        process_group_identifier, _ = process_model.modified_process_model_identifier().rsplit(":", 1)
        initial_url = (
            f"/v1.0/public/messages/submit/{process_group_identifier}:bounty_start_multiple_forms?execution_mode=synchronous"
        )
        response = client.post(
            initial_url,
            data=json.dumps(
                {"firstName": "MyName"},
            ),
            content_type="application/json",
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json is not None
        assert "form" in response.json
        assert "confirmation_message_markdown" in response.json
        assert "task_guid" in response.json
        assert "process_instance_id" in response.json
        assert response.json["form"] == {
            "form_schema": {
                "description": "Hey, MyName. Thanks for telling us who you are. Just one more field.",
                "properties": {"lastName": {"title": "Last name", "type": "string"}},
                "title": "Information request, part deux",
                "type": "object",
            },
            "form_ui_schema": {"lastName": {"ui:autoFocus": True}},
            "instructions_for_end_user": "## Enter your last name MyName",
        }
        assert response.json["confirmation_message_markdown"] is None

        task_guid = response.json["task_guid"]
        assert task_guid is not None
        process_instance_id = response.json["process_instance_id"]
        assert process_instance_id is not None

        second_form_url = f"/v1.0/public/tasks/{process_instance_id}/{task_guid}?execution_mode=synchronous"
        response = client.put(
            second_form_url,
            data=json.dumps(
                {"lastName": "MyLastName"},
            ),
            content_type="application/json",
            headers=headers,
        )

        assert response.status_code == 200
        assert response.json is not None
        assert "form" in response.json
        assert "confirmation_message_markdown" in response.json
        assert "task_guid" in response.json
        assert "process_instance_id" in response.json
        assert response.json["form"] is None
        assert response.json["confirmation_message_markdown"] == "# Thanks\n\nWe hear you. Your name is **MyName MyLastName**."
        assert response.json["task_guid"] is None
        assert response.json["process_instance_id"] == process_instance_id

        process_instance = ProcessInstanceModel.query.filter_by(id=process_instance_id).first()
        assert process_instance.status == ProcessInstanceStatus.user_input_required.value

    def test_can_complete_complete_a_guest_task(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        admin_user = self.find_or_create_user("admin")
        group_info: list[GroupPermissionsDict] = [
            {
                "users": [],
                "name": app.config["SPIFFWORKFLOW_BACKEND_DEFAULT_PUBLIC_USER_GROUP"],
                "permissions": [{"actions": ["create", "read", "update"], "uri": "/public/*"}],
            },
            {
                "users": [admin_user.username],
                "name": "admin",
                "permissions": [{"actions": ["all"], "uri": "/*"}],
            },
        ]
        AuthorizationService.refresh_permissions(group_info)

        process_group_id = "my_process_group"
        process_model_id = "test-allow-guest"
        bpmn_file_location = "test-allow-guest"
        process_model = self.create_group_and_model_with_bpmn(
            client,
            admin_user,
            process_group_id=process_group_id,
            process_model_id=process_model_id,
            bpmn_file_location=bpmn_file_location,
        )

        admin_headers = self.logged_in_headers(admin_user)
        response = self.create_process_instance_from_process_model_id_with_api(client, process_model.id, admin_headers)
        assert response.json is not None
        process_instance_id = response.json["id"]

        response = client.post(
            f"/v1.0/process-instances/{self.modify_process_identifier_for_path_param(process_model.id)}/{process_instance_id}/run",
            headers=admin_headers,
        )
        assert response.status_code == 200

        task_model = TaskModel.query.filter_by(process_instance_id=process_instance_id, state="READY").first()
        assert task_model is not None
        first_task_guid = task_model.guid

        response = client.get(
            f"/v1.0/public/tasks/{process_instance_id}/{first_task_guid}",
        )
        assert response.status_code == 200
        assert response.json is not None
        assert response.json["form"] == {"form_schema": None, "form_ui_schema": None, "instructions_for_end_user": ""}
        assert response.json["confirmation_message_markdown"] is None
        assert response.json["task_guid"] == first_task_guid
        assert response.json["process_instance_id"] == process_instance_id

        headers_dict = dict(response.headers)
        assert "Set-Cookie" in headers_dict
        cookie = headers_dict["Set-Cookie"]
        cookie_split = cookie.split(";")
        access_token = [cookie for cookie in cookie_split if cookie.startswith("access_token=")][0]
        assert access_token is not None
        re_result = re.match(r"^access_token=[\w_\.-]+$", access_token)
        assert re_result is not None
        user_header = {"Authorization": "Bearer " + access_token.split("=")[1]}

        response = client.put(
            f"/v1.0/public/tasks/{process_instance_id}/{first_task_guid}?execution_mode=synchronous",
            data="{}",
            content_type="application/json",
            headers=user_header,
        )
        assert response.status_code == 200
        assert response.json is not None
        assert response.json["form"] == {"instructions_for_end_user": "We have instructions."}
        assert response.json["confirmation_message_markdown"] is None
        assert response.json["task_guid"] is not None
        assert response.json["task_guid"] != first_task_guid
        assert response.json["process_instance_id"] == process_instance_id

        second_task_guid = response.json["task_guid"]
        response = client.put(
            f"/v1.0/public/tasks/{process_instance_id}/{second_task_guid}?execution_mode=synchronous",
            data="{}",
            content_type="application/json",
            headers=user_header,
        )
        assert response.status_code == 200
        assert response.json is not None
        assert response.json["form"] is None
        assert response.json["confirmation_message_markdown"] == "You have completed the task."
        assert response.json["task_guid"] is None
        assert response.json["process_instance_id"] == process_instance_id

        process_instance = ProcessInstanceModel.query.filter_by(id=process_instance_id).first()
        assert process_instance is not None
        assert process_instance.status == ProcessInstanceStatus.complete.value
