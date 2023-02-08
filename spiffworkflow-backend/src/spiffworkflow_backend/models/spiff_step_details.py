"""Spiff_step_details."""
from dataclasses import dataclass

from sqlalchemy import ForeignKey
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import deferred

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel


@dataclass
class SpiffStepDetailsModel(SpiffworkflowBaseDBModel):
    """SpiffStepDetailsModel."""

    __tablename__ = "spiff_step_details"
    __table_args__ = (
        UniqueConstraint(
            "process_instance_id", "spiff_step", name="process_instance_id_spiff_step"
        ),
    )

    id: int = db.Column(db.Integer, primary_key=True)
    process_instance_id: int = db.Column(
        ForeignKey(ProcessInstanceModel.id), nullable=False  # type: ignore
    )
    spiff_step: int = db.Column(db.Integer, nullable=False)
    task_json: dict = deferred(db.Column(db.JSON, nullable=False))  # type: ignore
    task_id: str | None = db.Column(db.String(50), nullable=False)
    bpmn_task_identifier: str | None = db.Column(db.String(255), nullable=False)

    # timestamp: float = db.Column(db.DECIMAL(17, 6), nullable=False)
    engine_step_start_in_seconds: float | None = db.Column(db.DECIMAL(17, 6))
    engine_step_end_in_seconds: float | None = db.Column(db.DECIMAL(17, 6))
