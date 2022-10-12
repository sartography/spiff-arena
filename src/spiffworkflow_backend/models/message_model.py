"""Message_model."""
from flask_bpmn.models.db import db
from flask_bpmn.models.db import SpiffworkflowBaseDBModel


class MessageModel(SpiffworkflowBaseDBModel):
    """MessageModel."""

    __tablename__ = "message_model"

    id = db.Column(db.Integer, primary_key=True)
    identifier = db.Column(db.String(50), unique=True, index=True)
    name = db.Column(db.String(50), unique=True, index=True)
