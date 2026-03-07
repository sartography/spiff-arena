from dataclasses import dataclass

from sqlalchemy import ForeignKey

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel


@dataclass
class WorkflowBlobStorageModel(SpiffworkflowBaseDBModel):
    __tablename__ = "workflow_blob_storage"

    process_instance_id: int = db.Column(ForeignKey(ProcessInstanceModel.id), primary_key=True)  # type: ignore
    workflow_data: dict = db.Column(db.JSON, nullable=False)
    serializer_version: str = db.Column(db.String(50), nullable=True)
    created_at_in_seconds: int = db.Column(db.Integer, nullable=False)
    updated_at_in_seconds: int = db.Column(db.Integer, nullable=False)
