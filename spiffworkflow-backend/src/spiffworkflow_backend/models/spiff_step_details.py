"""Spiff_step_details."""
from dataclasses import dataclass

from flask_bpmn.models.db import db
from flask_bpmn.models.db import SpiffworkflowBaseDBModel
from sqlalchemy.orm import deferred


@dataclass
class SpiffStepDetailsModel(SpiffworkflowBaseDBModel):
    """SpiffStepDetailsModel."""

    __tablename__ = "spiff_step_details"
    id: int = db.Column(db.Integer, primary_key=True)
    process_instance_id: int = db.Column(db.Integer, nullable=False)
    spiff_step: int = db.Column(db.Integer, nullable=False)
    task_json: str | None = deferred(db.Column(db.JSON, nullable=False))  # type: ignore
    timestamp: float = db.Column(db.DECIMAL(17, 6), nullable=False)
    completed_by_user_id: int = db.Column(db.Integer, nullable=True)
