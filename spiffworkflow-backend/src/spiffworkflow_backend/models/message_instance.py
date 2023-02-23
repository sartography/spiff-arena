"""Message_instance."""
import enum
from dataclasses import dataclass
from typing import Any
from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.event import listens_for
from sqlalchemy.orm import Session, relationship
from sqlalchemy.orm import validates

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.user import UserModel
from SpiffWorkflow.bpmn.PythonScriptEngine import PythonScriptEngine  # type: ignore


class MessageTypes(enum.Enum):
    """MessageTypes."""

    send = "send"
    receive = "receive"


class MessageStatuses(enum.Enum):
    """MessageStatuses."""

    ready = "ready"
    running = "running"
    completed = "completed"
    failed = "failed"


@dataclass
class MessageInstanceModel(SpiffworkflowBaseDBModel):
    """Messages from a process instance that are ready to send to a receiving task."""

    __tablename__ = "message_instance"

    id: int = db.Column(db.Integer, primary_key=True)
    process_instance_id: int = db.Column(ForeignKey(ProcessInstanceModel.id), nullable=True)  # type: ignore
    name: str = db.Column(db.String(255))
    message_type: str = db.Column(db.String(20), nullable=False)
    payload: dict = db.Column(db.JSON)
    status: str = db.Column(db.String(20), nullable=False, default="ready")
    user_id: int = db.Column(ForeignKey(UserModel.id), nullable=False)  # type: ignore
    user = relationship("UserModel")
    counterpart_id: int = db.Column(db.Integer) # Not enforcing self-referential foreign key so we can delete messages.
    failure_cause: str = db.Column(db.Text())
    updated_at_in_seconds: int = db.Column(db.Integer)
    created_at_in_seconds: int = db.Column(db.Integer)
    correlations = relationship("MessageInstanceCorrelationModel", back_populates="message_instance")

    @validates("message_type")
    def validate_message_type(self, key: str, value: Any) -> Any:
        """Validate_message_type."""
        return self.validate_enum_field(key, value, MessageTypes)

    @validates("status")
    def validate_status(self, key: str, value: Any) -> Any:
        """Validate_status."""
        return self.validate_enum_field(key, value, MessageStatuses)

    def correlates(self, other_message_instance: Any, expression_engine: PythonScriptEngine) -> bool:
        # This must be a receive message, and the other must be a send (otherwise we reverse the call)
        # We evaluate the other messages payload and run our correlation's
        # retrieval expressions against it, then compare it against our
        # expected values -- IF we don't have an expected value, we accept
        # any non-erroring result from the retrieval expression.
        if self.name != other_message_instance.name:
            return False
        if self.message_type == MessageTypes.receive.value:
            if other_message_instance.message_type != MessageTypes.send.value:
                return False
            payload = other_message_instance.payload
            for corr in self.correlations:
                try:
                    result = expression_engine._evaluate(corr.retrieval_expression, payload)
                except Exception as e:
                    # the failure of a payload evaluation may not mean that matches for these
                    # message instances can't happen with other messages.  So don't error up.
                    # fixme:  Perhaps log some sort of error.
                    return False
                if corr.expected_value is None:
                    continue  # We will accept any value
                elif corr.expected_value != str(result): # fixme:  Don't require conversion to string
                    return False
            return True
        elif other_message_instance.message_type == MessageTypes.receive.value:
            return other_message_instance.correlates(self, expression_engine)
        return False

# This runs for ALL db flushes for ANY model, not just this one even if it's in the MessageInstanceModel class
# so this may not be worth it or there may be a better way to do it
#
# https://stackoverflow.com/questions/32555829/flask-validates-decorator-multiple-fields-simultaneously/33025472#33025472
# https://docs.sqlalchemy.org/en/14/orm/session_events.html#before-flush
@listens_for(Session, "before_flush")  # type: ignore
def ensure_failure_cause_is_set_if_message_instance_failed(
    session: Any, _flush_context: Optional[Any], _instances: Optional[Any]
) -> None:
    """Ensure_failure_cause_is_set_if_message_instance_failed."""
    for instance in session.new:
        if isinstance(instance, MessageInstanceModel):
            if instance.status == "failed" and instance.failure_cause is None:
                raise ValueError(
                    f"{instance.__class__.__name__}: failure_cause must be set if"
                    " status is failed"
                )
