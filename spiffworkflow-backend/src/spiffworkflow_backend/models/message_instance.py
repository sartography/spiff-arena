"""Message_instance."""
import enum
from dataclasses import dataclass
from typing import Any, Self
from typing import Optional
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.event import listens_for
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Session
from sqlalchemy.orm import validates

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.message_correlation_message_instance import message_correlation_message_instance_table
from spiffworkflow_backend.models.message_model import MessageModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel



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
    process_instance_id: int = db.Column(ForeignKey(ProcessInstanceModel.id), nullable=False)  # type: ignore
    message_model_id: int = db.Column(ForeignKey(MessageModel.id), nullable=False)
    message_model = db.relationship("MessageModel")
    message_correlations = db.relationship("MessageCorrelationModel",
                                   secondary=message_correlation_message_instance_table,
                                   backref="message_instances",
                                   cascade="all,delete")

    message_type: str = db.Column(db.String(20), nullable=False)
    payload: str = db.Column(db.JSON)
    status: str = db.Column(db.String(20), nullable=False, default="ready")
    failure_cause: str = db.Column(db.Text())
    updated_at_in_seconds: int = db.Column(db.Integer)
    created_at_in_seconds: int = db.Column(db.Integer)

    @validates("message_type")
    def validate_message_type(self, key: str, value: Any) -> Any:
        """Validate_message_type."""
        return self.validate_enum_field(key, value, MessageTypes)

    @validates("status")
    def validate_status(self, key: str, value: Any) -> Any:
        """Validate_status."""
        return self.validate_enum_field(key, value, MessageStatuses)

    def correlation_dictionary(self):
        correlation_dict = {}
        for c in self.message_correlations:
            correlation_dict[c.name]=c.value
        return correlation_dict

    def correlates(self, other_message_instance: Self) -> bool:
        if other_message_instance.message_model_id != self.message_model_id:
            return False
        return self.correlates_with_dictionary(other_message_instance.correlation_dictionary())

    def correlates_with_dictionary(self, dict: dict) -> bool:
        """Returns true if the given dictionary matches the correlation
        names and values connected to this message instance"""
        for c in self.message_correlations:
            # Fixme: Maybe we should look at typing the correlations and not forcing them to strings?
            if c.name in dict and str(dict[c.name]) == c.value:
                continue
            else:
                return False
        return True

        corrs = {}



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
