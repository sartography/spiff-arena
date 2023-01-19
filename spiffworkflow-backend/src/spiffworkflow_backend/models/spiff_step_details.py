"""Spiff_step_details."""
from dataclasses import dataclass

from sqlalchemy import ForeignKey
from sqlalchemy.orm import deferred

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel


@dataclass
class SpiffStepDetailsModel(SpiffworkflowBaseDBModel):
    """SpiffStepDetailsModel."""

    __tablename__ = "spiff_step_details"
    id: int = db.Column(db.Integer, primary_key=True)
    process_instance_id: int = db.Column(
        ForeignKey(ProcessInstanceModel.id), nullable=False  # type: ignore
    )
    # human_task_id: int = db.Column(
    #     ForeignKey(HumanTaskModel.id)  # type: ignore
    # )
    spiff_step: int = db.Column(db.Integer, nullable=False)
    task_json: dict = deferred(db.Column(db.JSON, nullable=False))  # type: ignore
    timestamp: float = db.Column(db.DECIMAL(17, 6), nullable=False)
    # completed_by_user_id: int = db.Column(db.Integer, nullable=True)
    # lane_assignment_id: Optional[int] = db.Column(
    #     ForeignKey(GroupModel.id), nullable=True
    # )
