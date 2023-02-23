"""Message_correlation."""
from dataclasses import dataclass

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.message_instance import MessageInstanceModel

@dataclass
class MessageInstanceCorrelationModel(SpiffworkflowBaseDBModel):
    """These are the correlations of a specific Message Instance - these will
     only exist on receive messages. It provides the expression to run on a
     send messages payload which must match the expected value to be considered
     a valid match.  If the expected value is null, then it does not need to
     match, but the expression should still evaluate and produce a result."""

    __tablename__ = "message_instance_correlation"
    __table_args__ = (
        db.UniqueConstraint(
            "message_instance_id",
            "name",
            name="message_instance_id_name_unique",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    message_instance_id = db.Column(
        ForeignKey(MessageInstanceModel.id), nullable=False, index=True
    )
    name: str = db.Column(db.String(50), nullable=False)
    expected_value: str = db.Column(db.String(255), nullable=True, index=True)
    retrieval_expression: str = db.Column(db.String(255))
    updated_at_in_seconds: int = db.Column(db.Integer)
    created_at_in_seconds: int = db.Column(db.Integer)
    message_instance = relationship("MessageInstanceModel", back_populates="correlations")