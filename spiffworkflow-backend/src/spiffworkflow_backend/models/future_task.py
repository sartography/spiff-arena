from dataclasses import dataclass
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel

@dataclass
class FutureTaskModel(SpiffworkflowBaseDBModel):
    __tablename__ = "future_task"

    id: int = db.Column(db.Integer, primary_key=True)
    guid: str = db.Column(db.String(36), nullable=False, unique=True)

    # WAITING, QUEUED, COMPLETE / delete it
    status: str = db.Column(db.String(50), index=True)

    run_at_in_seconds: int = db.Column(db.Integer)
    updated_at_in_seconds: int = db.Column(db.Integer)
    created_at_in_seconds: int = db.Column(db.Integer)
