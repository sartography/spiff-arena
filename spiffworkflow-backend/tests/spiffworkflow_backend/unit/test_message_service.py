"""Test_message_service."""
import pytest
from flask import Flask
from flask.testing import FlaskClient
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.message_instance import MessageInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.routes.messages_controller import message_send
from spiffworkflow_backend.services.message_service import MessageService
from spiffworkflow_backend.services.process_instance_processor import (
    ProcessInstanceProcessor,
)
from spiffworkflow_backend.services.process_instance_service import (
    ProcessInstanceService,
)


class TestMessageService(BaseTest):
    """TestMessageService."""

    def test_message_from_api_into_running_process(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test sending a message to a running process via the API.

        This example workflow will send a message called 'request_approval' and then wait for a response message
        of 'approval_result'.  This test assures that it will fire the message with the correct correlation properties
        and will respond only to a message called 'approval_result' that has the matching correlation properties,
        as sent by an API Call.
        """
        self.payload = {
            "customer_id": "Sartography",
            "po_number": 1001,
            "description": "We built a new feature for messages!",
            "amount": "100.00",
        }

        self.start_sender_process(client, with_super_admin_user)
        self.assure_a_message_was_sent()
        self.assure_there_is_a_process_waiting_on_a_message()

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
            .filter_by(process_instance_id=self.process_instance.id)
            .all()
        )
        assert len(waiting_messages) == 0

        # The process has completed
        assert self.process_instance.status == "complete"

    def test_single_conversation_between_two_processes(
        self,
        app: Flask,
        client: FlaskClient,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test messages between two different running processes using a single conversation.

        Assure that communication between two processes works the same as making a call through the API, here
        we have two process instances that are communicating with each other using one conversation about an
        Invoice whose details are defined in the following message payload
        """
        self.payload = {
            "customer_id": "Sartography",
            "po_number": 1001,
            "description": "We built a new feature for messages!",
            "amount": "100.00",
        }

        # Load up the definition for the receiving process (it has a message start event that should cause it to
        # fire when a unique message comes through.
        # Fire up the first process
        load_test_spec(
            "test_group/message_receive",
            process_model_source_directory="message_send_one_conversation",
            bpmn_file_name="message_receiver.bpmn",
        )

        # Now start the main process
        self.start_sender_process(client, with_super_admin_user)
        self.assure_a_message_was_sent()

        # This is typically called in a background cron process, so we will manually call it
        # here in the tests
        # The first time it is called, it will instantiate a new instance of the message_recieve process
        MessageService.correlate_all_message_instances()

        # The sender process should still be waiting on a message to be returned to it ...
        self.assure_there_is_a_process_waiting_on_a_message()

        # The second time we call ths process_message_isntances (again it would typically be running on cron)
        # it will deliver the message that was sent from the receiver back to the original sender.
        MessageService.correlate_all_message_instances()

        # But there should be no send message waiting for delivery, because
        # the message receiving process should pick it up instantly via
        # it's start event.
        waiting_messages = (
            MessageInstanceModel.query.filter_by(message_type="receive")
            .filter_by(status="ready")
            .filter_by(process_instance_id=self.process_instance.id)
            .all()
        )
        assert len(waiting_messages) == 0
        MessageService.correlate_all_message_instances()
        MessageService.correlate_all_message_instances()
        MessageService.correlate_all_message_instances()
        assert len(waiting_messages) == 0

        # The message sender process is complete
        assert self.process_instance.status == "complete"

        # The message receiver process is also complete
        message_receiver_process = ProcessInstanceModel.query.filter_by(
            process_model_identifier="test_group/message_receive"
        ).first()
        assert message_receiver_process.status == "complete"

    def start_sender_process(
        self, client: FlaskClient, with_super_admin_user: UserModel
    ) -> None:
        process_group_id = "test_group"
        self.create_process_group(
            client, with_super_admin_user, process_group_id, process_group_id
        )

        process_model = load_test_spec(
            "test_group/message",
            process_model_source_directory="message_send_one_conversation",
            bpmn_file_name="message_sender.bpmn",  # Slightly misnamed, it sends and receives
        )

        self.process_instance = ProcessInstanceService.create_process_instance_from_process_model_identifier(
            process_model.id,
            with_super_admin_user,
        )
        processor_send_receive = ProcessInstanceProcessor(self.process_instance)
        processor_send_receive.do_engine_steps(save=True)
        task = processor_send_receive.get_all_user_tasks()[0]
        human_task = self.process_instance.active_human_tasks[0]

        ProcessInstanceService.complete_form_task(
            processor_send_receive,
            task,
            self.payload,
            with_super_admin_user,
            human_task,
        )
        processor_send_receive.save()

    def assure_a_message_was_sent(self) -> None:
        # There should be one new send message for the given process instance.
        send_messages = (
            MessageInstanceModel.query.filter_by(message_type="send")
            .filter_by(process_instance_id=self.process_instance.id)
            .all()
        )
        assert len(send_messages) == 1
        send_message = send_messages[0]
        assert (
            send_message.payload == self.payload
        ), "The send message should match up with the payload"
        assert send_message.name == "Request Approval"
        assert send_message.status == "ready"

    def assure_there_is_a_process_waiting_on_a_message(self) -> None:
        # There should be one new send message for the given process instance.
        waiting_messages = (
            MessageInstanceModel.query.filter_by(message_type="receive")
            .filter_by(status="ready")
            .filter_by(process_instance_id=self.process_instance.id)
            .all()
        )
        assert len(waiting_messages) == 1
        waiting_message = waiting_messages[0]
        self.assure_correlation_properties_are_right(waiting_message)

    def assure_correlation_properties_are_right(
        self, message: MessageInstanceModel
    ) -> None:
        # Correlation Properties should match up
        po_curr = next(c for c in message.correlations if c.name == "po_number")
        customer_curr = next(
            c for c in message.correlations if c.name == "customer_id"
        )
        assert po_curr is not None
        assert customer_curr is not None
        assert po_curr.expected_value == "1001"
        assert customer_curr.expected_value == "Sartography"

    def test_can_send_message_to_multiple_process_models(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_can_send_message_to_multiple_process_models."""
        process_group_id = "test_group_multi"
        self.create_process_group(
            client, with_super_admin_user, process_group_id, process_group_id
        )

        process_model_sender = load_test_spec(
            "test_group/message_sender",
            process_model_source_directory="message_send_two_conversations",
            bpmn_file_name="message_sender",
        )
        load_test_spec(
            "test_group/message_receiver_one",
            process_model_source_directory="message_send_two_conversations",
            bpmn_file_name="message_receiver_one",
        )
        load_test_spec(
            "test_group/message_receiver_two",
            process_model_source_directory="message_send_two_conversations",
            bpmn_file_name="message_receiver_two",
        )

        user = self.find_or_create_user()

        process_instance_sender = ProcessInstanceService.create_process_instance_from_process_model_identifier(
            process_model_sender.id, user
        )

        processor_sender = ProcessInstanceProcessor(process_instance_sender)
        processor_sender.do_engine_steps()
        processor_sender.save()

        # At this point, the message_sender process has fired two different messages but those
        # processes have not started, and it is now paused, waiting for to receive a message. so
        # we should have two sends and a receive.
        assert (
            MessageInstanceModel.query.filter_by(
                process_instance_id=process_instance_sender.id
            ).count()
            == 3
        )
        assert (
            MessageInstanceModel.query.count() == 3
        )  # all messages are related to the instance
        orig_send_messages = MessageInstanceModel.query.filter_by(
            message_type="send"
        ).all()
        assert len(orig_send_messages) == 2
        assert MessageInstanceModel.query.filter_by(message_type="receive").count() == 1


        # process message instances
        MessageService.correlate_all_message_instances()
        # Once complete the original send messages should be completed and two new instances
        # should now exist, one for each of the process instances ...
#        for osm in orig_send_messages:
#            assert osm.status == "completed"

        process_instance_result = ProcessInstanceModel.query.all()
        assert len(process_instance_result) == 3
        process_instance_receiver_one = ProcessInstanceModel.query.filter_by(
            process_model_identifier="test_group/message_receiver_one"
        ).first()
        assert process_instance_receiver_one is not None
        process_instance_receiver_two = ProcessInstanceModel.query.filter_by(
            process_model_identifier="test_group/message_receiver_two"
        ).first()
        assert process_instance_receiver_two is not None

        # just make sure it's a different process instance
        assert (
            process_instance_receiver_one.process_model_identifier
            == "test_group/message_receiver_one"
        )
        assert process_instance_receiver_one.id != process_instance_sender.id
        assert process_instance_receiver_one.status == "complete"
        assert (
            process_instance_receiver_two.process_model_identifier
            == "test_group/message_receiver_two"
        )
        assert process_instance_receiver_two.id != process_instance_sender.id
        assert process_instance_receiver_two.status == "complete"

        message_instance_result = MessageInstanceModel.query.all()
        assert len(message_instance_result) == 7

        message_instance_receiver_one = [
            x
            for x in message_instance_result
            if x.process_instance_id == process_instance_receiver_one.id
        ][0]
        message_instance_receiver_two = [
            x
            for x in message_instance_result
            if x.process_instance_id == process_instance_receiver_two.id
        ][0]
        assert message_instance_receiver_one is not None
        assert message_instance_receiver_two is not None

        # Cause a currelation event
        MessageService.correlate_all_message_instances()
        # We have to run it a second time because instances are firing
        # more messages that need to be picked up.
        MessageService.correlate_all_message_instances()

        message_instance_result = MessageInstanceModel.query.all()
        assert len(message_instance_result) == 8
        for message_instance in message_instance_result:
            assert message_instance.status == "completed"

        process_instance_result = ProcessInstanceModel.query.all()
        assert len(process_instance_result) == 3
        for process_instance in process_instance_result:
            assert process_instance.status == "complete"
