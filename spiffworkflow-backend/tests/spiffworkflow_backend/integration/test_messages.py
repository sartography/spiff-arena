import pytest
from flask import Flask
from flask import g
from flask.testing import FlaskClient
from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.message_instance import MessageInstanceModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.routes.messages_controller import message_send
from spiffworkflow_backend.services.data_setup_service import DataSetupService
from spiffworkflow_backend.services.message_service import MessageService

from tests.spiffworkflow_backend.helpers.base_test import BaseTest


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
                {"payload": {"po_number": 1001, "customer_id": "jon"}},
            )

        # No error when calling with the correct parameters
        message_send(
            "Approval Result",
            {"payload": {"po_number": 1001, "customer_id": "Sartography"}},
        )

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


    def test_message_model_list_up_search (
            self,
            app: Flask,
            client: FlaskClient,
            with_db_and_bpmn_file_cleanup: None,
            with_super_admin_user: UserModel,
    ) -> None:
        self.copy_example_process_models()
        DataSetupService.save_all_process_models()
        response = client.get(
            f"/v1.0/message-models?relative_location=1-basic-concepts",
            headers=self.logged_in_headers(with_super_admin_user),
            content_type="application/json",
        )
        assert response.json is not None
        assert len(response.json["messages"]) == 4

        response = client.get(
            f"/v1.0/message-models?relative_location=",
            headers=self.logged_in_headers(with_super_admin_user),
            content_type="application/json",
        )
        assert response.json is not None
        assert len(response.json["messages"]) == 3, "should not have access to messages defined in a sub directory"


    def test_message_model_list_up_search (
            self,
            app: Flask,
            client: FlaskClient,
            with_db_and_bpmn_file_cleanup: None,
            with_super_admin_user: UserModel,
    ) -> None:
        self.copy_example_process_models()
        DataSetupService.save_all_process_models()

        updated_xml = MessageService.updateProcessModelXmlWithMessageDetails(
            process_model_xml,
            message_details
        )


