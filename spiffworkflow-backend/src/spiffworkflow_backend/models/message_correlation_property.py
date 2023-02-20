"""Message_correlation_property."""
from sqlalchemy import ForeignKey

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.message_model import MessageModel


class MessageCorrelationPropertyModel(SpiffworkflowBaseDBModel):
    """MessageCorrelationPropertyModel."""

    __tablename__ = "message_correlation_property"
    __table_args__ = (
        db.UniqueConstraint(
            "identifier",
            "message_model_id",
            name="message_correlation_property_unique",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    identifier = db.Column(db.String(50), index=True)
    message_model_id = db.Column(ForeignKey(MessageModel.id), nullable=False)
    updated_at_in_seconds: int = db.Column(db.Integer)
    created_at_in_seconds: int = db.Column(db.Integer)
    message_model = db.relationship("MessageModel", backref="correlation_properties")
