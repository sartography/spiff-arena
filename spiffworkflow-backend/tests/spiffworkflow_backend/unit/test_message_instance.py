"""Test_message_instance."""
import pytest
from flask import Flask
from flask_bpmn.models.db import db
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec

from spiffworkflow_backend.models.message_instance import MessageInstanceModel
from spiffworkflow_backend.models.message_model import MessageModel


class TestMessageInstance(BaseTest):
    """TestMessageInstance."""

    def test_can_create_message_instance(
        self, app: Flask, with_db_and_bpmn_file_cleanup: None
    ) -> None:
        """Test_can_create_message_instance."""
        message_model_identifier = "message_model_one"
        message_model = self.create_message_model(message_model_identifier)
        process_model = load_test_spec("hello_world")
        process_instance = self.create_process_instance_from_process_model(
            process_model, "waiting"
        )

        queued_message = MessageInstanceModel(
            process_instance_id=process_instance.id,
            message_type="send",
            message_model_id=message_model.id,
        )
        db.session.add(queued_message)
        db.session.commit()

        assert queued_message.status == "ready"
        assert queued_message.failure_cause is None

        queued_message_from_query = MessageInstanceModel.query.filter_by(  # type: ignore
            id=queued_message.id
        ).first()
        assert queued_message_from_query is not None

    def test_cannot_set_invalid_status(
        self, app: Flask, with_db_and_bpmn_file_cleanup: None
    ) -> None:
        """Test_cannot_set_invalid_status."""
        message_model_identifier = "message_model_one"
        message_model = self.create_message_model(message_model_identifier)
        process_model = load_test_spec("hello_world")
        process_instance = self.create_process_instance_from_process_model(
            process_model, "waiting"
        )

        with pytest.raises(ValueError) as exception:
            MessageInstanceModel(
                process_instance_id=process_instance.id,
                message_type="send",
                message_model_id=message_model.id,
                status="BAD_STATUS",
            )
        assert (
            str(exception.value) == "MessageInstanceModel: invalid status: BAD_STATUS"
        )

        queued_message = MessageInstanceModel(
            process_instance_id=process_instance.id,
            message_type="send",
            message_model_id=message_model.id,
        )
        db.session.add(queued_message)
        db.session.commit()

        with pytest.raises(ValueError) as exception:
            queued_message.status = "BAD_STATUS"
        assert (
            str(exception.value) == "MessageInstanceModel: invalid status: BAD_STATUS"
        )

    def test_cannot_set_invalid_message_type(
        self, app: Flask, with_db_and_bpmn_file_cleanup: None
    ) -> None:
        """Test_cannot_set_invalid_message_type."""
        message_model_identifier = "message_model_one"
        message_model = self.create_message_model(message_model_identifier)
        process_model = load_test_spec("hello_world")
        process_instance = self.create_process_instance_from_process_model(
            process_model, "waiting"
        )

        with pytest.raises(ValueError) as exception:
            MessageInstanceModel(
                process_instance_id=process_instance.id,
                message_type="BAD_MESSAGE_TYPE",
                message_model_id=message_model.id,
            )
        assert (
            str(exception.value)
            == "MessageInstanceModel: invalid message_type: BAD_MESSAGE_TYPE"
        )

        queued_message = MessageInstanceModel(
            process_instance_id=process_instance.id,
            message_type="send",
            message_model_id=message_model.id,
        )
        db.session.add(queued_message)
        db.session.commit()

        with pytest.raises(ValueError) as exception:
            queued_message.message_type = "BAD_MESSAGE_TYPE"
        assert (
            str(exception.value)
            == "MessageInstanceModel: invalid message_type: BAD_MESSAGE_TYPE"
        )

    def test_force_failure_cause_if_status_is_failure(
        self, app: Flask, with_db_and_bpmn_file_cleanup: None
    ) -> None:
        """Test_force_failure_cause_if_status_is_failure."""
        message_model_identifier = "message_model_one"
        message_model = self.create_message_model(message_model_identifier)
        process_model = load_test_spec("hello_world")
        process_instance = self.create_process_instance_from_process_model(
            process_model, "waiting"
        )

        queued_message = MessageInstanceModel(
            process_instance_id=process_instance.id,
            message_type="send",
            message_model_id=message_model.id,
            status="failed",
        )
        db.session.add(queued_message)
        with pytest.raises(ValueError) as exception:
            db.session.commit()
        assert (
            str(exception.value)
            == "MessageInstanceModel: failure_cause must be set if status is failed"
        )
        assert queued_message.id is None
        db.session.remove()  # type: ignore

        queued_message = MessageInstanceModel(
            process_instance_id=process_instance.id,
            message_type="send",
            message_model_id=message_model.id,
        )
        db.session.add(queued_message)
        db.session.commit()

        queued_message.status = "failed"
        queued_message.failure_cause = "THIS TEST FAILURE"
        db.session.add(queued_message)
        db.session.commit()
        assert queued_message.id is not None
        assert queued_message.failure_cause == "THIS TEST FAILURE"

    def create_message_model(self, message_model_identifier: str) -> MessageModel:
        """Create_message_model."""
        message_model = MessageModel(identifier=message_model_identifier)
        db.session.add(message_model)
        db.session.commit()
        return message_model
