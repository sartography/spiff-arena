"""Test_message_service."""
import pytest
from flask import Flask
from flask.testing import FlaskClient

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.routes.messages_controller import message_send
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec

from spiffworkflow_backend.models.message_correlation import MessageCorrelationModel
from spiffworkflow_backend.models.message_instance import MessageInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.message_service import MessageService
from spiffworkflow_backend.services.process_instance_processor import (
    ProcessInstanceProcessor,
)
from spiffworkflow_backend.services.process_instance_service import (
    ProcessInstanceService,
)


class TestMessageService(BaseTest):
    """TestMessageService."""

    def test_message_sent(
            self,
            app: Flask,
            client: FlaskClient,
            with_db_and_bpmn_file_cleanup: None,
            with_super_admin_user: UserModel,
    ) -> None:
        """This example workflow will send a message called 'request_approval' and then wait for a response messge
        of 'approval_result.  This test assures that it will fire the message with the correct correlation properties
        and will respond only to a message called "approval_result' that has the matching correlation properties."""
        process_group_id = "test_group"
        self.create_process_group(
            client, with_super_admin_user, process_group_id, process_group_id
        )

        process_model = load_test_spec(
            "test_group/message",
            process_model_source_directory="message",
            bpmn_file_name="message_send_receive.bpmn",
        )

        self.process_instance = ProcessInstanceService.create_process_instance_from_process_model_identifier(
            process_model.id,
            with_super_admin_user,
        )
        processor_send_receive = ProcessInstanceProcessor(self.process_instance)
        processor_send_receive.do_engine_steps(save=True)
        task = processor_send_receive.get_all_user_tasks()[0]
        human_task = self.process_instance.active_human_tasks[0]
        spiff_task = processor_send_receive.__class__.get_task_by_bpmn_identifier(
            human_task.task_name, processor_send_receive.bpmn_process_instance
        )
        self.payload = {
            "customer_id": "Sartography",
            "po_number": 1001,
            "description": "We build a new feature for messages!",
            "amount": "100.00"
        }

        ProcessInstanceService.complete_form_task(
            processor_send_receive,
            task,
            self.payload,
            with_super_admin_user,
            human_task,
        )
        processor_send_receive.save()
        self.assure_a_message_was_sent()
        self.assure_there_is_a_process_waiting_on_a_message()

        ## Should return an error when making an API call for the wrong po number
        with pytest.raises(ApiError):
            message_send("approval_result", {'payload': {'po_number' : 5001}})

        ## Sound return an error when making an API call for right po number, wrong client
        with pytest.raises(ApiError):
            message_send("approval_result", {'payload': {'po_number' : 1001, 'customer_id': 'jon'}})

        ## No error when calling with the correct parameters
        response = message_send("approval_result", {'payload': {'po_number' : 1001, 'customer_id': 'Sartography'}})

        ## There is no longer a waiting message
        waiting_messages = MessageInstanceModel.query. \
            filter_by(message_type = "receive"). \
            filter_by(process_instance_id = self.process_instance.id).all()
        assert len(waiting_messages) == 0

    def assure_a_message_was_sent(self):
        # There should be one new send message for the given process instance.
        send_messages = MessageInstanceModel.query. \
            filter_by(message_type = "send"). \
            filter_by(process_instance_id = self.process_instance.id).all()
        assert len(send_messages) == 1
        send_message = send_messages[0]

        # The payload should match because of how it is written in the Send task.
        assert send_message.payload == self.payload, "The send message should match up with the payload"
        assert send_message.message_model.identifier == "request_approval"
        assert send_message.status == "ready"
        assert len(send_message.message_correlations) == 2
        message_instance_result = MessageInstanceModel.query.all()
        self.assure_correlation_properties_are_right(send_message)

    def assure_there_is_a_process_waiting_on_a_message(self):
        # There should be one new send message for the given process instance.
        waiting_messages = MessageInstanceModel.query. \
            filter_by(message_type = "receive"). \
            filter_by(process_instance_id = self.process_instance.id).all()
        assert len(waiting_messages) == 1
        waiting_message = waiting_messages[0]
        self.assure_correlation_properties_are_right(waiting_message)

    def assure_correlation_properties_are_right(self, message):
        # Correlation Properties should match up
        po_curr = next(c for c in message.message_correlations if c.name == "po_number")
        customer_curr = next(c for c in message.message_correlations if c.name == "customer_id")
        assert po_curr is not None
        assert customer_curr is not None
        assert po_curr.value == '1001'
        assert customer_curr.value == "Sartography"

