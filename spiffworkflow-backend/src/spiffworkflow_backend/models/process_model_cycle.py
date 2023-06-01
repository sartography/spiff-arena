from dataclasses import dataclass

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db


@dataclass
class ProcessModelCycleModel(SpiffworkflowBaseDBModel):
    __tablename__ = "process_model_cycle"

    id: int = db.Column(db.Integer, primary_key=True)
    process_model_identifier: str = db.Column(db.String(255), nullable=False, index=True)
    cycle_count: int = db.Column(db.Integer)
    duration_in_seconds: int = db.Column(db.Integer)
    current_cycle: int = db.Column(db.Integer)
    updated_at_in_seconds: int = db.Column(db.Integer)
    created_at_in_seconds: int = db.Column(db.Integer)
