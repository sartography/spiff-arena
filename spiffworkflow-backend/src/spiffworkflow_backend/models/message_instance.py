import enum
from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import Any

from flask import current_app
from SpiffWorkflow.bpmn.script_engine import PythonScriptEngine  # type: ignore
from sqlalchemy import ForeignKey
from sqlalchemy.event import listens_for
from sqlalchemy.orm import Session
from sqlalchemy.orm import relationship
from sqlalchemy.orm import validates

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.user import UserModel

if TYPE_CHECKING:
    from spiffworkflow_backend.models.message_instance_correlation import (  # noqa: F401,I001
        MessageInstanceCorrelationRuleModel,
    )


class MessageTypes(enum.Enum):
    send = "send"
    receive = "receive"


class MessageStatuses(enum.Enum):
    ready = "ready"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


@dataclass
class MessageInstanceModel(SpiffworkflowBaseDBModel):
    """Messages from a process instance that are ready to send to a receiving task."""

    __tablename__ = "message_instance"

    id: int = db.Column(db.Integer, primary_key=True)
    process_instance_id: int = db.Column(ForeignKey(ProcessInstanceModel.id), nullable=True, index=True)  # type: ignore
    name: str = db.Column(db.String(255))
    message_type: str = db.Column(db.String(20), nullable=False)
    # Only Send Messages have a payload
    payload: dict = db.Column(db.JSON)
    # The correlation keys of the process at the time the message was created.
    correlation_keys: dict = db.Column(db.JSON)
    status: str = db.Column(db.String(20), nullable=False, default="ready", index=True)
    user_id: int = db.Column(ForeignKey(UserModel.id), nullable=True, index=True)  # type: ignore
    user = relationship("UserModel")
    counterpart_id: int = db.Column(db.Integer)  # Not enforcing self-referential foreign key so we can delete messages.
    failure_cause: str = db.Column(db.Text())
    updated_at_in_seconds: int = db.Column(db.Integer)
    created_at_in_seconds: int = db.Column(db.Integer)
    correlation_rules = relationship("MessageInstanceCorrelationRuleModel", back_populates="message_instance", cascade="delete")

    @validates("message_type")
    def validate_message_type(self, key: str, value: Any) -> Any:
        return self.validate_enum_field(key, value, MessageTypes)

    @validates("status")
    def validate_status(self, key: str, value: Any) -> Any:
        return self.validate_enum_field(key, value, MessageStatuses)

    @classmethod
    def split_modified_message_name(cls, modified_message_name: str) -> tuple[str, str]:
        message_name_array = modified_message_name.split(":")
        message_name = message_name_array.pop()
        process_group_identifier = "/".join(message_name_array)
        return (message_name, process_group_identifier)

    def correlates(self, other: Any, expression_engine: PythonScriptEngine) -> bool:
        """Returns true if the this Message correlates with the given message.

        This must be a 'receive' message, and the other must be a 'send' or vice/versa.
        If both messages have identical correlation_keys, they are a match.  Otherwise
        we check through this messages correlation properties and use the retrieval expressions
        to extract the correlation keys from the send's payload, and verify that these
        match up with correlation keys on this message.
        """
        if self.is_send() and other.is_receive():
            # Flip the call.
            return other.correlates(self, expression_engine)  # type: ignore

        if self.name != other.name:
            return False
        if not self.is_receive():
            return False
        if isinstance(self.correlation_keys, dict) and self.correlation_keys == other.correlation_keys:
            # We know we have a match, and we can just return if we don't have to figure out the key
            return True

        if self.correlation_keys == {}:
            # Then there is nothing more to match on -- we accept any message with the given name.
            return True

        # Loop over the receives' correlation keys - if any of the keys fully match, then we match.
        for expected_values in self.correlation_keys.values():
            if self.payload_matches_expected_values(other.payload, expected_values, expression_engine):
                return True
        return False

    def is_receive(self) -> bool:
        return self.message_type == MessageTypes.receive.value

    def is_send(self) -> bool:
        return self.message_type == MessageTypes.send.value

    def payload_matches_expected_values(
        self,
        payload: dict,
        expected_values: dict,
        expression_engine: PythonScriptEngine,
    ) -> bool:
        """Compares the payload of a 'send' message against a single correlation key's expected values."""
        for correlation_key in self.correlation_rules:
            expected_value = expected_values.get(correlation_key.name, None)
            if expected_value is None:  # This key is not required for this instance to match.
                continue
            try:
                result = expression_engine.environment.evaluate(correlation_key.retrieval_expression, payload)
            except Exception as e:
                # the failure of a payload evaluation may not mean that matches for these
                # message instances can't happen with other messages.  So don't error up.
                current_app.logger.warning(
                    "Error evaluating correlation key when comparing send and receive messages. "
                    + f"Mesage name: '{self.name}'. Receive mesage id: '{self.id}'. "
                    + f"Expression {correlation_key.retrieval_expression} failed with the error: "
                    + str(e)
                )
                return False
            if result != expected_value:
                return False
        return True


# This runs for ALL db flushes for ANY model, not just this one even if it's in the MessageInstanceModel class
# so this may not be worth it or there may be a better way to do it
#
# https://stackoverflow.com/questions/32555829/flask-validates-decorator-multiple-fields-simultaneously/33025472#33025472
# https://docs.sqlalchemy.org/en/14/orm/session_events.html#before-flush


@listens_for(Session, "before_flush")  # type: ignore
def ensure_failure_cause_is_set_if_message_instance_failed(
    session: Any, _flush_context: Any | None, _instances: Any | None
) -> None:
    for instance in session.new:
        if isinstance(instance, MessageInstanceModel):
            if instance.status == "failed" and instance.failure_cause is None:
                raise ValueError(f"{instance.__class__.__name__}: failure_cause must be set if status is failed")
