"""Spiff_step_details."""
from dataclasses import dataclass
from flask_bpmn.models.db import db
from flask_bpmn.models.db import SpiffworkflowBaseDBModel

from sqlalchemy import ForeignKey

from spiffworkflow_backend.models.process_instance import ProcessInstanceModel


@dataclass
class ProcessInstanceMetadataModel(SpiffworkflowBaseDBModel):
    """ProcessInstanceMetadataModel."""

    __tablename__ = "process_instance_metadata"
    __table_args__ = (
        db.UniqueConstraint(
            "process_instance_id", "key", name="process_instance_metadata_unique"
        ),
    )

    id: int = db.Column(db.Integer, primary_key=True)
    process_instance_id: int = db.Column(
        ForeignKey(ProcessInstanceModel.id), nullable=False  # type: ignore
    )
    key: str = db.Column(db.String(255), nullable=False)
    value: str = db.Column(db.String(255), nullable=False)

    updated_at_in_seconds: int = db.Column(db.Integer, nullable=False)
    created_at_in_seconds: int = db.Column(db.Integer, nullable=False)
