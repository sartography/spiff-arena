"""Message_correlation_property."""
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel


class MessageTriggerableProcessModel(SpiffworkflowBaseDBModel):
    """MessageTriggerableProcessModel."""

    __tablename__ = "message_triggerable_process_model"

    id = db.Column(db.Integer, primary_key=True)
    message_name: str = db.Column(db.String(255))
    process_model_identifier: str = db.Column(db.String(50), nullable=False, index=True)
    updated_at_in_seconds: int = db.Column(db.Integer)
    created_at_in_seconds: int = db.Column(db.Integer)
