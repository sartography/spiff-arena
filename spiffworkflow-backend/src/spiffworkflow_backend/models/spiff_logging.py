"""Spiff_logging."""
from dataclasses import dataclass
from typing import Optional

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel


@dataclass
class SpiffLoggingModel(SpiffworkflowBaseDBModel):
    """SpiffLoggingModel."""

    __tablename__ = "spiff_logging"
    id: int = db.Column(db.Integer, primary_key=True)
    process_instance_id: int = db.Column(db.Integer, nullable=False)
    bpmn_process_identifier: str = db.Column(db.String(255), nullable=False)
    bpmn_task_identifier: str = db.Column(db.String(255), nullable=False)
    bpmn_task_name: str = db.Column(db.String(255), nullable=True)
    bpmn_task_type: str = db.Column(db.String(255), nullable=True)
    spiff_task_guid: str = db.Column(db.String(50), nullable=False)
    timestamp: float = db.Column(db.DECIMAL(17, 6), nullable=False)
    message: Optional[str] = db.Column(db.String(255), nullable=True)
    current_user_id: int = db.Column(db.Integer, nullable=True)
    spiff_step: int = db.Column(db.Integer, nullable=False)
