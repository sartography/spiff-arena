from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import ForeignKey
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import relationship

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db


@dataclass
class MessageModel(SpiffworkflowBaseDBModel):
    __tablename__ = "message"
    __table_args__ = (UniqueConstraint("identifier", "location", name="message_identifier_location_unique"),)

    id: int = db.Column(db.Integer, primary_key=True)
    identifier: str = db.Column(db.String(255), index=True, nullable=False)
    location: str = db.Column(db.String(255), index=True, nullable=False)
    schema: dict = db.Column(db.JSON, nullable=False)
    updated_at_in_seconds: int = db.Column(db.Integer, nullable=False)
    created_at_in_seconds: int = db.Column(db.Integer, nullable=False)

    correlation_properties = relationship("MessageCorrelationPropertyModel", cascade="delete")


@dataclass
class MessageCorrelationPropertyModel(SpiffworkflowBaseDBModel):
    __tablename__ = "message_correlation_property"
    __table_args__ = (UniqueConstraint("message_id", "identifier", name="message_correlation_property_unique"),)

    id: int = db.Column(db.Integer, primary_key=True)
    message_id: int = db.Column(
        ForeignKey(MessageModel.id, name="message_correlation_property_message_id_fk"),  # type: ignore
        nullable=False,
        index=True,
    )
    identifier: str = db.Column(db.String(255), index=True, nullable=False)
    retrieval_expression: str = db.Column(db.String(255), nullable=False)
    updated_at_in_seconds: int = db.Column(db.Integer, nullable=False)
    created_at_in_seconds: int = db.Column(db.Integer, nullable=False)

    message = relationship("MessageModel", back_populates="correlation_properties")
