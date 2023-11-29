from dataclasses import dataclass

from sqlalchemy import ForeignKey

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel


@dataclass
class ProcessInstanceMetadataModel(SpiffworkflowBaseDBModel):
    __tablename__ = "process_instance_metadata"
    __table_args__ = (db.UniqueConstraint("process_instance_id", "key", name="process_instance_metadata_unique"),)

    id: int = db.Column(db.Integer, primary_key=True)
    process_instance_id: int = db.Column(ForeignKey(ProcessInstanceModel.id), nullable=False, index=True)  # type: ignore
    key: str = db.Column(db.String(255), nullable=False, index=True)
    value: str = db.Column(db.String(255), nullable=False)

    updated_at_in_seconds: int = db.Column(db.Integer, nullable=False)
    created_at_in_seconds: int = db.Column(db.Integer, nullable=False)
