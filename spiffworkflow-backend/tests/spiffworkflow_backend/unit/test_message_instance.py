import pytest
from flask import Flask
from starlette.testclient import TestClient

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.message_instance import MessageInstanceModel
from spiffworkflow_backend.models.message_instance_correlation import MessageInstanceCorrelationRuleModel
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.services.process_instance_script_engine import CustomBpmnScriptEngine
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestMessageInstance(BaseTest):
    def setup_message_tests(self) -> ProcessModelInfo:
        process_model_id = "testk_group/hello_world"
        bpmn_file_name = "hello_world.bpmn"
        bpmn_file_location = "hello_world"
        process_model = load_test_spec(
            process_model_id=process_model_id,
            bpmn_file_name=bpmn_file_name,
            process_model_source_directory=bpmn_file_location,
        )
        return process_model

    def test_can_create_message_instance(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        message_name = "Message Model One"
        process_model = self.setup_message_tests()
        process_instance = self.create_process_instance_from_process_model(process_model, "waiting")

        queued_message = MessageInstanceModel(
            process_instance_id=process_instance.id,
            user_id=process_instance.process_initiator_id,
            message_type="send",
            name=message_name,
            payload={"Word": "Eat At Mashita's, its delicious!"},
        )
        db.session.add(queued_message)
        db.session.commit()

        assert queued_message.status == "ready"
        assert queued_message.failure_cause is None

        queued_message_from_query = MessageInstanceModel.query.filter_by(id=queued_message.id).first()  # type: ignore
        assert queued_message_from_query is not None

    def test_cannot_set_invalid_status(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        message_name = "message_model_one"
        process_model = self.setup_message_tests()
        process_instance = self.create_process_instance_from_process_model(process_model, "waiting")

        with pytest.raises(ValueError) as exception:
            MessageInstanceModel(
                process_instance_id=process_instance.id,
                user_id=process_instance.process_initiator_id,
                message_type="send",
                name=message_name,
                status="BAD_STATUS",
            )
        assert str(exception.value) == "MessageInstanceModel: invalid status: BAD_STATUS"

        queued_message = MessageInstanceModel(
            process_instance_id=process_instance.id,
            user_id=process_instance.process_initiator_id,
            message_type="send",
            name=message_name,
        )
        db.session.add(queued_message)
        db.session.commit()

        with pytest.raises(ValueError) as exception:
            queued_message.status = "BAD_STATUS"
        assert str(exception.value) == "MessageInstanceModel: invalid status: BAD_STATUS"

    def test_cannot_set_invalid_message_type(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        message_name = "message_model_one"
        process_model = self.setup_message_tests()
        process_instance = self.create_process_instance_from_process_model(process_model, "waiting")

        with pytest.raises(ValueError) as exception:
            MessageInstanceModel(
                process_instance_id=process_instance.id,
                user_id=process_instance.process_initiator_id,
                message_type="BAD_MESSAGE_TYPE",
                name=message_name,
            )
        assert str(exception.value) == "MessageInstanceModel: invalid message_type: BAD_MESSAGE_TYPE"

        queued_message = MessageInstanceModel(
            process_instance_id=process_instance.id,
            user_id=process_instance.process_initiator_id,
            message_type="send",
            name=message_name,
        )
        db.session.add(queued_message)
        db.session.commit()

        with pytest.raises(ValueError) as exception:
            queued_message.message_type = "BAD_MESSAGE_TYPE"
        assert str(exception.value) == "MessageInstanceModel: invalid message_type: BAD_MESSAGE_TYPE"

    def test_force_failure_cause_if_status_is_failure(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        message_name = "message_model_one"
        process_model = self.setup_message_tests()
        process_instance = self.create_process_instance_from_process_model(process_model, "waiting")

        queued_message = MessageInstanceModel(
            process_instance_id=process_instance.id,
            user_id=process_instance.process_initiator_id,
            message_type="send",
            name=message_name,
            status="failed",
        )
        db.session.add(queued_message)
        with pytest.raises(ValueError) as exception:
            db.session.commit()
        assert str(exception.value) == "MessageInstanceModel: failure_cause must be set if status is failed"
        assert queued_message.id is None
        db.session.remove()  # type: ignore

        queued_message = MessageInstanceModel(
            process_instance_id=process_instance.id,
            user_id=process_instance.process_initiator_id,
            message_type="send",
            name=message_name,
        )
        db.session.add(queued_message)
        db.session.commit()

        queued_message.status = "failed"
        queued_message.failure_cause = "THIS TEST FAILURE"
        db.session.add(queued_message)
        db.session.commit()
        assert queued_message.id is not None
        assert queued_message.failure_cause == "THIS TEST FAILURE"

    def _create_receive_with_rules(
        self,
        process_instance_id: int,
        user_id: int,
        correlation_keys: dict,
        rules: list[tuple[str, str, list[str]]],
    ) -> MessageInstanceModel:
        receive_message = MessageInstanceModel(
            process_instance_id=process_instance_id,
            user_id=user_id,
            message_type="receive",
            name="assessment_outcome",
            correlation_keys=correlation_keys,
        )
        db.session.add(receive_message)
        for name, retrieval_expression, correlation_key_names in rules:
            db.session.add(
                MessageInstanceCorrelationRuleModel(
                    message_instance=receive_message,
                    name=name,
                    retrieval_expression=retrieval_expression,
                    correlation_key_names=correlation_key_names,
                )
            )
        db.session.commit()
        return receive_message

    def test_does_not_correlate_on_a_key_no_rule_applies_to(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        """A correlation key established by another message in the receiving scope is not a wildcard.

        The receive message's correlation_keys hold the whole workflow scope's correlations, which can
        include keys from other messages (e.g. a boundary event active alongside a receive task).  A key
        that none of this message's own correlation properties apply to must not count as a "full match",
        otherwise any send with the right name gets delivered to an arbitrary process instance.
        """
        process_model = self.setup_message_tests()
        process_instance = self.create_process_instance_from_process_model(process_model, "waiting")

        receive_message = self._create_receive_with_rules(
            process_instance.id,
            process_instance.process_initiator_id,
            correlation_keys={
                "ProcessUuid": {"process_uuid_property": "uuid-instance-a"},
                # Established in the same scope by a different message (boundary event); this
                # message has no rule for it.
                "AwaitedEvent": {"awaited_event_property": "event-instance-a"},
            },
            rules=[("process_uuid_property", "process_uuid", ["ProcessUuid"])],
        )

        send_for_another_instance = MessageInstanceModel(
            process_instance_id=process_instance.id,
            user_id=process_instance.process_initiator_id,
            message_type="send",
            name="assessment_outcome",
            payload={"process_uuid": "uuid-instance-b"},
        )
        db.session.add(send_for_another_instance)
        db.session.commit()
        assert receive_message.correlates(send_for_another_instance, CustomBpmnScriptEngine()) is False

        send_for_this_instance = MessageInstanceModel(
            process_instance_id=process_instance.id,
            user_id=process_instance.process_initiator_id,
            message_type="send",
            name="assessment_outcome",
            payload={"process_uuid": "uuid-instance-a"},
        )
        db.session.add(send_for_this_instance)
        db.session.commit()
        assert receive_message.correlates(send_for_this_instance, CustomBpmnScriptEngine()) is True

    def test_correlates_on_name_alone_when_message_has_no_rules(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        """A message with no correlation properties still correlates by name, even when the scope has keys."""
        process_model = self.setup_message_tests()
        process_instance = self.create_process_instance_from_process_model(process_model, "waiting")

        receive_message = self._create_receive_with_rules(
            process_instance.id,
            process_instance.process_initiator_id,
            correlation_keys={"SomeKey": {"some_property": "some-value"}},
            rules=[],
        )
        send_message = MessageInstanceModel(
            process_instance_id=process_instance.id,
            user_id=process_instance.process_initiator_id,
            message_type="send",
            name="assessment_outcome",
            payload={"unrelated": "payload"},
        )
        db.session.add(send_message)
        db.session.commit()
        assert receive_message.correlates(send_message, CustomBpmnScriptEngine()) is True
