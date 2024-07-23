from dataclasses import dataclass
from typing import TypedDict

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db


class ProcessInstanceMigrationDetailDict(TypedDict):
    initial_git_revision: str | None
    target_git_revision: str | None
    initial_bpmn_process_hash: str
    target_bpmn_process_hash: str


@dataclass
class ProcessInstanceMigrationDetailModel(SpiffworkflowBaseDBModel):
    __tablename__ = "process_instance_migration_detail"
    id: int = db.Column(db.Integer, primary_key=True)

    process_instance_event_id: int = db.Column(ForeignKey("process_instance_event.id"), nullable=False, index=True)
    process_instance_event = relationship("ProcessInstanceEventModel")  # type: ignore

    initial_git_revision: str | None = db.Column(db.String(64), nullable=True)
    target_git_revision: str | None = db.Column(db.String(64), nullable=True)
    initial_bpmn_process_hash: str = db.Column(db.String(64), nullable=False)
    target_bpmn_process_hash: str = db.Column(db.String(64), nullable=False)
