"""Message_correlation_message_instance."""
from dataclasses import dataclass

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel

from sqlalchemy import ForeignKey

from spiffworkflow_backend.models.message_correlation import MessageCorrelationModel
from spiffworkflow_backend.models.message_instance import MessageInstanceModel


@dataclass
class MessageCorrelationMessageInstanceModel(SpiffworkflowBaseDBModel):
    """MessageCorrelationMessageInstanceModel."""

    __tablename__ = "message_correlation_message_instance"

    __table_args__ = (
        db.UniqueConstraint(
            "message_instance_id",
            "message_correlation_id",
            name="message_correlation_message_instance_unique",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    message_instance_id = db.Column(
        ForeignKey(MessageInstanceModel.id), nullable=False, index=True  # type: ignore
    )
    message_correlation_id = db.Column(
        ForeignKey(MessageCorrelationModel.id), nullable=False, index=True
    )
