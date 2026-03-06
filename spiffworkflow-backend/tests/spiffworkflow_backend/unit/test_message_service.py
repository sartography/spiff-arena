import time
from uuid import UUID

from flask import Flask
from flask import g
from starlette.testclient import TestClient

from spiffworkflow_backend.helpers.spiff_enum import ProcessInstanceExecutionMode
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.message_instance import MessageInstanceModel
from spiffworkflow_backend.models.message_triggerable_process_model import MessageTriggerableProcessModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
from spiffworkflow_backend.models.process_instance_queue import ProcessInstanceQueueModel
from spiffworkflow_backend.services.message_service import MessageService
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService
from spiffworkflow_backend.services.spec_file_service import SpecFileService
from spiffworkflow_backend.services.workflow_execution_service import WorkflowExecutionServiceError
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestMessageService(BaseTest):
    def test_messages_feb_24(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        """Test messages between two different running processes using a single conversation.

        Check that communication between two processes works the same as making a call through the API, here
        we have two process instances that are communicating with each other using one conversation
        """

        # Load up the definition for the receiving process
        load_test_spec(
            "test_group/message_test_1",
            process_model_source_directory="message_feb24",
            bpmn_file_name="message-test-1.bpmn",
        )

        process_model = load_test_spec(
            "test_group/test_message_process",
            process_model_source_directory="message_feb24",
            bpmn_file_name="test-message-process.bpmn",
        )

        process_instance = self.create_process_instance_from_process_model(process_model)
        processor_send_receive = ProcessInstanceProcessor(process_instance)
        processor_send_receive.do_engine_steps(save=True)

        # This is typically called in a background cron process, so we will manually call it
        # here in the tests
        # The first time it is called, it will instantiate a new instance of the message_recieve process
        MessageService.correlate_all_message_instances()

        # The second time we call ths process_message_isntances (again it would typically be running on cron)
        # it will deliver the message that was sent from the receiver back to the original sender.
        MessageService.correlate_all_message_instances()

        # Assure that the messages all have correlation keys.
        message_instances = MessageInstanceModel.query.filter_by(message_type="receive").all()
        uid = message_instances[0].correlation_keys["MainCorrelationKey"]["uid"]
        assert len(message_instances) == 4
        for message_instance in message_instances:
            assert message_instance.correlation_keys == {"MainCorrelationKey": {"uid": uid}}

    def test_receive_message_will_have_correlation_keys(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_model = load_test_spec(
            "test_group/test_message_process",
            process_model_source_directory="message",
            bpmn_file_name="message-receive.bpmn",
        )

        process_instance = self.create_process_instance_from_process_model(process_model)
        processor_send_receive = ProcessInstanceProcessor(process_instance)
        processor_send_receive.do_engine_steps(save=True)

        # This is typically called in a background cron process, so we will manually call it
        MessageService.correlate_all_message_instances()
        MessageService.correlate_all_message_instances()

        # Assure that we have one message receive waiting, and that it's correlations are properly set.
        message_instances = MessageInstanceModel.query.all()
        assert len(message_instances) == 1
        assert message_instances[0].correlation_keys == {"MainCorrelationKey": {"uid": 1}}

    def test_receive_message_is_canceled_if_process_is_no_longer_waiting(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_model = load_test_spec(
            "test_group/test_message_process",
            process_model_source_directory="message",
            bpmn_file_name="message-receive-cancel.bpmn",
        )
        user = self.find_or_create_user("initiator_user")
        process_instance = self.create_process_instance_from_process_model(process_model, user=user)
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)

        # This is typically called in a background cron process, so we will manually call it
        MessageService.correlate_all_message_instances()
        MessageService.correlate_all_message_instances()

        # Assure that we have one message receive waiting
        message_instances = MessageInstanceModel.query.filter_by(message_type="receive", status="ready").all()
        assert len(message_instances) == 1

        # Complete the manual task, which means the message should no longer be waiting.
        assert len(process_instance.active_human_tasks) == 1
        human_task_one = process_instance.active_human_tasks[0]
        spiff_manual_task = processor.bpmn_process_instance.get_task_from_id(UUID(human_task_one.task_id))
        assert len(process_instance.active_human_tasks) == 1, "expected 1 active human task"
        ProcessInstanceService.complete_form_task(processor, spiff_manual_task, {}, user, human_task_one)

        # Assure that we no longer have a message waiting.
        message_instances = MessageInstanceModel.query.filter_by(message_type="receive", status="ready").all()
        assert len(message_instances) == 0

    def test_single_conversation_between_two_processes(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        """Test messages between two different running processes using a single conversation.

        Assure that communication between two processes works the same as making a call through the API, here
        we have two process instances that are communicating with each other using one conversation about an
        Invoice whose details are defined in the following message payload
        """
        payload = {
            "customer_id": "Sartography",
            "po_number": 1001,
            "description": "We built a new feature for messages!",
            "amount": "100.00",
        }

        # Load up the definition for the receiving process
        # It has a message start event that should cause it to fire when a unique message comes through
        # Fire up the first process
        load_test_spec(
            "test_group/message_receive",
            process_model_source_directory="message_send_one_conversation",
            bpmn_file_name="message_receiver.bpmn",
        )

        # Now start the main process
        process_instance = self.start_sender_process(client, payload, "test_between_processes")
        self.assure_a_message_was_sent(process_instance, payload)

        # This is typically called in a background cron process, so we will manually call it
        # here in the tests
        # The first time it is called, it will instantiate a new instance of the message_recieve process
        MessageService.correlate_all_message_instances()

        # The sender process should still be waiting on a message to be returned to it ...
        self.assure_there_is_a_process_waiting_on_a_message(process_instance)

        # The second time we call ths process_message_isntances (again it would typically be running on cron)
        # it will deliver the message that was sent from the receiver back to the original sender.
        MessageService.correlate_all_message_instances()

        # But there should be no send message waiting for delivery, because
        # the message receiving process should pick it up instantly via
        # it's start event.
        waiting_messages = (
            MessageInstanceModel.query.filter_by(message_type="receive")
            .filter_by(status="ready")
            .filter_by(process_instance_id=process_instance.id)
            .order_by(MessageInstanceModel.id)
            .all()
        )
        assert len(waiting_messages) == 0
        MessageService.correlate_all_message_instances()
        MessageService.correlate_all_message_instances()
        MessageService.correlate_all_message_instances()
        assert len(waiting_messages) == 0

        # The message sender process is complete
        assert process_instance.status == "complete"

        # The message receiver process is also complete
        message_receiver_process = (
            ProcessInstanceModel.query.filter_by(process_model_identifier="test_group/message_receive")
            .order_by(ProcessInstanceModel.id)
            .first()
        )
        assert message_receiver_process.status == "complete"

        message_instances = MessageInstanceModel.query.all()
        assert len(message_instances) == 4
        for message_instance in message_instances:
            assert message_instance.correlation_keys == {"invoice": {"po_number": 1001, "customer_id": "Sartography"}}

    def test_start_process_with_message_when_failure(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        """Assure we get a valid error when trying to start a process, and that process fails for some reason."""

        # Load up the definition for the receiving process
        # It has a message start event that should cause it to fire when a unique message comes through
        # Fire up the first process
        load_test_spec(
            "test_group/message-start-with-error",
            process_model_source_directory="message-start-with-error",
            bpmn_file_name="message-start-with-error.bpmn",
        )

        # Now send in the message
        user = self.find_or_create_user()
        message_triggerable_process_model = MessageTriggerableProcessModel.query.filter_by(
            message_name="test_bad_process"
        ).first()
        assert message_triggerable_process_model is not None

        MessageInstanceModel(
            message_type="send",
            name="test_bad_process",
            payload={},
            user_id=user.id,
        )
        g.user = user
        try:
            MessageService.run_process_model_from_message("test_bad_process", {}, ProcessInstanceExecutionMode.synchronous.value)
        except WorkflowExecutionServiceError as e:
            assert "The process instance encountered an error and failed after starting." in e.notes

    def test_can_send_message_to_multiple_process_models(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        # self.create_process_group_with_api(client, with_super_admin_user, process_group_id, process_group_id)

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
        assert MessageInstanceModel.query.filter_by(process_instance_id=process_instance_sender.id).count() == 3
        assert MessageInstanceModel.query.count() == 3  # all messages are related to the instance
        orig_send_messages = MessageInstanceModel.query.filter_by(message_type="send").all()
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
        process_instance_receiver_one = (
            ProcessInstanceModel.query.filter_by(process_model_identifier="test_group/message_receiver_one")
            .order_by(ProcessInstanceModel.id)
            .first()
        )
        assert process_instance_receiver_one is not None
        process_instance_receiver_two = (
            ProcessInstanceModel.query.filter_by(process_model_identifier="test_group/message_receiver_two")
            .order_by(ProcessInstanceModel.id)
            .first()
        )
        assert process_instance_receiver_two is not None

        # just make sure it's a different process instance
        assert process_instance_receiver_one.process_model_identifier == "test_group/message_receiver_one"
        assert process_instance_receiver_one.id != process_instance_sender.id
        assert process_instance_receiver_one.status == "complete"
        assert process_instance_receiver_two.process_model_identifier == "test_group/message_receiver_two"
        assert process_instance_receiver_two.id != process_instance_sender.id
        assert process_instance_receiver_two.status == "complete"

        message_instance_result = (
            MessageInstanceModel.query.order_by(MessageInstanceModel.id).order_by(MessageInstanceModel.id).all()
        )
        assert len(message_instance_result) == 7

        message_instance_receiver_one = [
            x for x in message_instance_result if x.process_instance_id == process_instance_receiver_one.id
        ][0]
        message_instance_receiver_two = [
            x for x in message_instance_result if x.process_instance_id == process_instance_receiver_two.id
        ][0]
        assert message_instance_receiver_one is not None
        assert message_instance_receiver_two is not None

        # Cause a currelation event
        MessageService.correlate_all_message_instances()
        # We have to run it a second time because instances are firing
        # more messages that need to be picked up.
        MessageService.correlate_all_message_instances()

        message_instance_result = (
            MessageInstanceModel.query.order_by(MessageInstanceModel.id).order_by(MessageInstanceModel.id).all()
        )
        assert len(message_instance_result) == 8
        for message_instance in message_instance_result:
            assert message_instance.status == "completed"

        process_instance_result = ProcessInstanceModel.query.order_by(ProcessInstanceModel.id).all()
        assert len(process_instance_result) == 3
        for process_instance in process_instance_result:
            assert process_instance.status == "complete"

    def test_can_send_to_correct_start_event_if_there_are_multiple(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        load_test_spec(
            "test_group/multiple_message_start_events",
            process_model_source_directory="multiple_message_start_events",
        )
        user = self.find_or_create_user()
        message_triggerable_process_model = MessageTriggerableProcessModel.query.filter_by(
            message_name="travel_start_test_v2"
        ).first()
        assert message_triggerable_process_model is not None

        MessageService.start_process_with_message(message_triggerable_process_model, user)
        message_instances = MessageInstanceModel.query.all()
        assert len(message_instances) == 1
        assert message_instances[0].name == "travel_start_test_v2"

    def test_can_send_a_message_with_non_persistent_process_instance(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_model_sender = load_test_spec(
            "test_group/simple-message-send",
            process_model_source_directory="simple-message-send-receive",
            bpmn_file_name="simple-message-send-receive.bpmn",
        )
        load_test_spec(
            "test_group/simple-message-receive",
            process_model_source_directory="simple-message-send-receive",
            bpmn_file_name="message_start_event.bpmn",
        )

        message_triggerable_process_model = MessageTriggerableProcessModel.query.filter_by(message_name="message_one").first()
        assert message_triggerable_process_model is not None

        processor = ProcessInstanceService.create_and_run_process_instance(
            process_model=process_model_sender,
            persistence_level="none",
        )
        assert processor.process_instance_model.process_model_identifier == "test_group/simple-message-send"

        # ensure we commit the message instances
        db.session.commit()

        message_instances = MessageInstanceModel.query.all()
        assert len(message_instances) == 1

        MessageService.correlate_all_message_instances()

        process_instances = ProcessInstanceModel.query.all()
        assert len(process_instances) == 1
        assert process_instances[0].status == ProcessInstanceStatus.complete.value
        assert process_instances[0].process_model_identifier == "test_group/simple-message-receive"

        message_instances = MessageInstanceModel.query.all()
        assert len(message_instances) == 2
        mi_statuses = [mi.status for mi in message_instances]
        assert mi_statuses == ["completed", "completed"]

    def test_can_delete_message_start_events_from_database_if_model_no_longer_references_it(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_model_without_message_start_event = load_test_spec(
            "test_group/sample",
            process_model_source_directory="sample",
        )
        old_message_triggerable_process = MessageTriggerableProcessModel(
            message_name="travel_start_test_v2",
            process_model_identifier=process_model_without_message_start_event.id,
            file_name=process_model_without_message_start_event.primary_file_name,
        )
        db.session.add(old_message_triggerable_process)
        db.session.commit()
        message_triggerable_process_model = MessageTriggerableProcessModel.query.filter_by(
            message_name="travel_start_test_v2"
        ).first()
        assert message_triggerable_process_model is not None
        assert message_triggerable_process_model.process_model_identifier == process_model_without_message_start_event.id

        assert process_model_without_message_start_event.primary_file_name is not None
        primary_file_contents = SpecFileService.get_data(
            process_model_without_message_start_event, process_model_without_message_start_event.primary_file_name
        )
        SpecFileService.update_file(
            process_model_without_message_start_event,
            process_model_without_message_start_event.primary_file_name,
            primary_file_contents,
        )
        message_triggerable_process_model = MessageTriggerableProcessModel.query.filter_by(
            message_name="travel_start_test_v2"
        ).first()
        assert message_triggerable_process_model is None

    def test_correlate_can_handle_process_instance_already_locked(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        # self.create_process_group_with_api(client, with_super_admin_user, process_group_id, process_group_id)

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

        process_instance = ProcessInstanceService.create_process_instance_from_process_model_identifier(
            process_model_sender.id, user
        )

        processor_sender = ProcessInstanceProcessor(process_instance)
        processor_sender.do_engine_steps(save=True)

        # At this point, the message_sender process has fired two different messages but those
        # processes have not started, and it is now paused, waiting for to receive a message. so
        # we should have two sends and a receive.
        assert MessageInstanceModel.query.filter_by(process_instance_id=process_instance.id).count() == 3
        assert MessageInstanceModel.query.count() == 3  # all messages are related to the instance
        orig_send_messages = MessageInstanceModel.query.filter_by(message_type="send").all()
        assert len(orig_send_messages) == 2
        assert MessageInstanceModel.query.filter_by(message_type="receive").count() == 1

        queue_entry = ProcessInstanceQueueModel.query.filter_by(process_instance_id=process_instance.id).first()
        assert queue_entry is not None
        queue_entry.locked_by = "test:test_waiting"
        queue_entry.locked_at_seconds = round(time.time())
        db.session.add(queue_entry)
        db.session.commit()

        MessageService.correlate_all_message_instances()

        assert ProcessInstanceModel.query.count() == 3
        MessageService.correlate_all_message_instances()

        message_send_instances = MessageInstanceModel.query.filter_by(name="Message Response Two", message_type="send").all()
        assert len(message_send_instances) == 1
        message_send_instance = message_send_instances[0]
        assert message_send_instance.status == "ready"
        assert message_send_instance.failure_cause is None

        message_receive_instances = MessageInstanceModel.query.filter_by(
            name="Message Response Two", message_type="receive"
        ).all()
        assert len(message_receive_instances) == 1
        message_receive_instance = message_receive_instances[0]
        assert message_receive_instance.status == "ready"
        assert message_receive_instance.failure_cause is None
