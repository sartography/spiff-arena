import json

import pytest
from flask import Flask
from flask import g
from flask.testing import FlaskClient
from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.message_instance import MessageInstanceModel
from spiffworkflow_backend.routes.messages_controller import message_send
from spiffworkflow_backend.services.authorization_service import AuthorizationService
from spiffworkflow_backend.services.authorization_service import GroupPermissionsDict
from spiffworkflow_backend.services.user_service import UserService

from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestMessages(BaseTest):
    def test_message_from_api_into_running_process(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        """Test sending a message to a running process via the API.

        This example workflow will send a message called 'request_approval' and then wait for a response message
        of 'approval_result'.  This test assures that it will fire the message with the correct correlation properties
        and will respond only to a message called 'approval_result' that has the matching correlation properties,
        as sent by an API Call.
        """
        payload = {
            "customer_id": "Sartography",
            "po_number": 1001,
            "description": "We built a new feature for messages!",
            "amount": "100.00",
        }
        process_instance = self.start_sender_process(client, payload, "test_from_api")
        self.assure_a_message_was_sent(process_instance, payload)
        self.assure_there_is_a_process_waiting_on_a_message(process_instance)
        g.user = process_instance.process_initiator

        # Make an API call to the service endpoint, but use the wrong po number
        with pytest.raises(ApiError):
            message_send("Approval Result", {"payload": {"po_number": 5001}})

        # Should return an error when making an API call for right po number, wrong client
        with pytest.raises(ApiError):
            message_send(
                "Approval Result",
                {"po_number": 1001, "customer_id": "jon"},
            )

        # No error when calling with the correct parameters
        response = message_send(
            "Approval Result",
            {"po_number": 1001, "customer_id": "Sartography"},
        )

        # The response's task data should also match up with the correlation keys.
        response_json = response.json
        assert response_json["task_data"]["po_number"] == 1001
        assert response_json["task_data"]["customer_id"] == "Sartography"

        # There is no longer a waiting message
        waiting_messages = (
            MessageInstanceModel.query.filter_by(message_type="receive")
            .filter_by(status="ready")
            .filter_by(process_instance_id=process_instance.id)
            .all()
        )
        assert len(waiting_messages) == 0
        # The process has completed
        assert process_instance.status == "complete"

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
        user = UserService.create_public_user()
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
            headers=self.logged_in_headers(user, extra_token_payload={"public": True}),
            data=json.dumps(
                {"hey": "my_val"},
            ),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json is not None
        assert "task_data" in response.json
        assert "process_instance" in response.json
        assert response.json["process_instance"]["status"] == "complete"
