from dataclasses import dataclass
from datetime import datetime

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db


@dataclass
class APILogModel(SpiffworkflowBaseDBModel):
    __tablename__ = "api_log"

    id: int = db.Column(db.Integer, primary_key=True)
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow)
    endpoint: str = db.Column(db.String(255))
    method: str = db.Column(db.String(10))
    request_body: dict | None = db.Column(db.JSON)
    response_body: dict | None = db.Column(db.JSON)
    status_code: int = db.Column(db.Integer)
    process_instance_id: int | None = db.Column(db.Integer, nullable=True)
    duration_ms: int = db.Column(db.Integer)
