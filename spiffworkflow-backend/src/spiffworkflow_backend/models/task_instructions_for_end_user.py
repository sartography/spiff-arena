from dataclasses import dataclass

from sqlalchemy import ForeignKey

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db


@dataclass
class TaskInstructionsForEndUserModel(SpiffworkflowBaseDBModel):
    __tablename__ = "task_instructions_for_end_user"

    task_guid: str = db.Column(db.String(36), primary_key=True)
    instruction: str = db.Column(db.String(255), nullable=False)
    process_instance_id: int = db.Column(ForeignKey("process_instance.id"), nullable=False, index=True)

    updated_at_in_seconds: int = db.Column(db.Integer)
    created_at_in_seconds: int = db.Column(db.Integer)
