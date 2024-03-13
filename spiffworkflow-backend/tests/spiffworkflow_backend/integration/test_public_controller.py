import json

from flask import Flask
from flask.testing import FlaskClient
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
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
        assert "form_schema" in response.json
        assert "form_ui_schema" in response.json
        assert response.json["form_schema"]["title"] == "Form for message start event"

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
                {"hey": "my_val"},
            ),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json is not None
        assert "form" in response.json
        assert "instructions" in response.json
        assert "task_guid" in response.json
        assert response.json["form"] is None
        assert response.json["instructions"] is None
        assert response.json["task_guid"] is None

    def test_can_submit_to_public_message_submit_and_get_and_submit_subsequent_form(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        user = self.find_or_create_user("testuser1")
        headers = self.logged_in_headers(user, extra_token_payload={"public": True})
        group_info: list[GroupPermissionsDict] = [
            {
                "users": [user.username],
                "name": app.config["SPIFFWORKFLOW_BACKEND_DEFAULT_PUBLIC_USER_GROUP"],
                "permissions": [{"actions": ["create", "read", "update"], "uri": "/public/*"}],
            }
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
        assert "instructions" in response.json
        assert "task_guid" in response.json
        assert "process_instance_id" in response.json
        assert response.json["form"] == {
            "form_schema": {
                "description": "HELLO MyName",
                "properties": {"lastName": {"title": "Last name", "type": "string"}},
                "title": "Your results",
                "type": "object",
            },
            "form_ui_schema": {},
        }
        assert response.json["instructions"] is None

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
        assert "instructions" in response.json
        assert "task_guid" in response.json
        assert "process_instance_id" in response.json
        assert response.json["form"] is None
        assert response.json["instructions"] is None
        assert response.json["task_guid"] is None
        assert response.json["process_instance_id"] == process_instance_id

        process_instance = ProcessInstanceModel.query.filter_by(id=process_instance_id).first()
        assert process_instance.status == ProcessInstanceStatus.complete.value
