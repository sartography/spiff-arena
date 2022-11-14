"""Message_correlation."""
from dataclasses import dataclass
from typing import TYPE_CHECKING

from flask_bpmn.models.db import db
from flask_bpmn.models.db import SpiffworkflowBaseDBModel
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from spiffworkflow_backend.models.message_correlation_property import (
    MessageCorrelationPropertyModel,
)
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel

if TYPE_CHECKING:
    from spiffworkflow_backend.models.message_correlation_message_instance import (  # noqa: F401
        MessageCorrelationMessageInstanceModel,
    )


@dataclass
class MessageCorrelationModel(SpiffworkflowBaseDBModel):
    """Message Correlations to relate queued messages together."""

    __tablename__ = "message_correlation"
    __table_args__ = (
        db.UniqueConstraint(
            "process_instance_id",
            "message_correlation_property_id",
            "name",
            name="message_instance_id_name_unique",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    process_instance_id = db.Column(
        ForeignKey(ProcessInstanceModel.id), nullable=False, index=True  # type: ignore
    )
    message_correlation_property_id = db.Column(
        ForeignKey(MessageCorrelationPropertyModel.id), nullable=False, index=True
    )
    name = db.Column(db.String(255), nullable=False, index=True)
    value = db.Column(db.String(255), nullable=False, index=True)
    updated_at_in_seconds: int = db.Column(db.Integer)
    created_at_in_seconds: int = db.Column(db.Integer)

    message_correlation_property = relationship(
        "MessageCorrelationPropertyModel"
    )
    message_correlations_message_instances = relationship(
        "MessageCorrelationMessageInstanceModel", cascade="delete"
    )
