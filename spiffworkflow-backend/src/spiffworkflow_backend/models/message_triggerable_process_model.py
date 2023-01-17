"""Message_correlation_property."""
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel

from sqlalchemy import ForeignKey

from spiffworkflow_backend.models.message_model import MessageModel


class MessageTriggerableProcessModel(SpiffworkflowBaseDBModel):
    """MessageTriggerableProcessModel."""

    __tablename__ = "message_triggerable_process_model"

    id = db.Column(db.Integer, primary_key=True)
    message_model_id = db.Column(
        ForeignKey(MessageModel.id), nullable=False, unique=True
    )
    process_model_identifier: str = db.Column(db.String(50), nullable=False, index=True)

    updated_at_in_seconds: int = db.Column(db.Integer)
    created_at_in_seconds: int = db.Column(db.Integer)
