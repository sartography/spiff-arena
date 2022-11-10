"""Test_message_service."""
from flask import Flask
from flask.testing import FlaskClient
from spiffworkflow_backend.models.message_correlation import MessageCorrelationModel
from spiffworkflow_backend.models.message_correlation_message_instance import (
    MessageCorrelationMessageInstanceModel,
)
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
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestMessageService(BaseTest):
    """TestMessageService."""

    def test_can_send_message_to_waiting_message(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_can_send_message_to_waiting_message."""
        process_group_id = "test_group"
        self.create_process_group(
            client, with_super_admin_user, process_group_id, process_group_id
        )

        load_test_spec(
            "test_group/message_receiver",
            process_model_source_directory="message_send_one_conversation",
            bpmn_file_name="message_receiver.bpmn",
        )
        process_model_sender = load_test_spec(
            "test_group/message_sender",
            process_model_source_directory="message_send_one_conversation",
            bpmn_file_name="message_sender.bpmn",
        )

        process_instance_sender = ProcessInstanceService.create_process_instance(
            process_model_sender.id,
            with_super_admin_user,
        )

        processor_sender = ProcessInstanceProcessor(process_instance_sender)
        processor_sender.do_engine_steps()
        processor_sender.save()

        message_instance_result = MessageInstanceModel.query.all()
        assert len(message_instance_result) == 2
        # ensure both message instances are for the same process instance
        # it will be send_message and receive_message_response
        assert (
            message_instance_result[0].process_instance_id
            == message_instance_result[1].process_instance_id
        )

        message_instance_sender = message_instance_result[0]
        assert message_instance_sender.process_instance_id == process_instance_sender.id
        message_correlations = MessageCorrelationModel.query.all()
        assert len(message_correlations) == 2
        assert message_correlations[0].process_instance_id == process_instance_sender.id
        message_correlations_message_instances = (
            MessageCorrelationMessageInstanceModel.query.all()
        )
        assert len(message_correlations_message_instances) == 4
        assert (
            message_correlations_message_instances[0].message_instance_id
            == message_instance_sender.id
        )
        assert (
            message_correlations_message_instances[1].message_instance_id
            == message_instance_sender.id
        )
        assert (
            message_correlations_message_instances[2].message_instance_id
            == message_instance_result[1].id
        )
        assert (
            message_correlations_message_instances[3].message_instance_id
            == message_instance_result[1].id
        )

        # process first message
        MessageService.process_message_instances()
        assert message_instance_sender.status == "completed"

        process_instance_result = ProcessInstanceModel.query.all()

        assert len(process_instance_result) == 2
        process_instance_receiver = process_instance_result[1]

        # just make sure it's a different process instance
        assert process_instance_receiver.id != process_instance_sender.id
        assert process_instance_receiver.status == "complete"

        message_instance_result = MessageInstanceModel.query.all()
        assert len(message_instance_result) == 3
        message_instance_receiver = message_instance_result[1]
        assert message_instance_receiver.id != message_instance_sender.id
        assert message_instance_receiver.status == "ready"

        # process second message
        MessageService.process_message_instances()

        message_instance_result = MessageInstanceModel.query.all()
        assert len(message_instance_result) == 3
        for message_instance in message_instance_result:
            assert message_instance.status == "completed"

        process_instance_result = ProcessInstanceModel.query.all()
        assert len(process_instance_result) == 2
        for process_instance in process_instance_result:
            assert process_instance.status == "complete"

    def test_can_send_message_to_multiple_process_models(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_can_send_message_to_multiple_process_models."""
        process_group_id = "test_group"
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

        process_instance_sender = ProcessInstanceService.create_process_instance(
            process_model_sender.id,
            user,
            # process_group_identifier=process_model_sender.process_group_id,
        )

        processor_sender = ProcessInstanceProcessor(process_instance_sender)
        processor_sender.do_engine_steps()
        processor_sender.save()

        message_instance_result = MessageInstanceModel.query.all()
        assert len(message_instance_result) == 3
        # ensure both message instances are for the same process instance
        # it will be send_message and receive_message_response
        assert (
            message_instance_result[0].process_instance_id
            == message_instance_result[1].process_instance_id
        )

        message_instance_sender = message_instance_result[0]
        assert message_instance_sender.process_instance_id == process_instance_sender.id
        message_correlations = MessageCorrelationModel.query.all()
        assert len(message_correlations) == 4
        assert message_correlations[0].process_instance_id == process_instance_sender.id
        message_correlations_message_instances = (
            MessageCorrelationMessageInstanceModel.query.all()
        )
        assert len(message_correlations_message_instances) == 6
        assert (
            message_correlations_message_instances[0].message_instance_id
            == message_instance_sender.id
        )
        assert (
            message_correlations_message_instances[1].message_instance_id
            == message_instance_sender.id
        )
        assert (
            message_correlations_message_instances[2].message_instance_id
            == message_instance_result[1].id
        )
        assert (
            message_correlations_message_instances[3].message_instance_id
            == message_instance_result[1].id
        )

        # process first message
        MessageService.process_message_instances()
        assert message_instance_sender.status == "completed"

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
        assert len(message_instance_result) == 5

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
        assert message_instance_receiver_one.id != message_instance_sender.id
        assert message_instance_receiver_one.status == "ready"
        assert message_instance_receiver_two.id != message_instance_sender.id
        assert message_instance_receiver_two.status == "ready"

        # process second message
        MessageService.process_message_instances()
        MessageService.process_message_instances()

        message_instance_result = MessageInstanceModel.query.all()
        assert len(message_instance_result) == 6
        for message_instance in message_instance_result:
            assert message_instance.status == "completed"

        process_instance_result = ProcessInstanceModel.query.all()
        assert len(process_instance_result) == 3
        for process_instance in process_instance_result:
            assert process_instance.status == "complete"
