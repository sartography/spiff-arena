from dataclasses import dataclass
from datetime import datetime
from datetime import timezone

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db


@dataclass
class APILogModel(SpiffworkflowBaseDBModel):
    __tablename__ = "api_log"

    id: int = db.Column(db.Integer, primary_key=True)
    created_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    endpoint: str = db.Column(db.String(255), index=True)
    method: str = db.Column(db.String(10), index=True)
    request_body: dict | None = db.Column(db.JSON)
    query_params: dict | None = db.Column(db.JSON)
    response_body: dict | None = db.Column(db.JSON)
    status_code: int = db.Column(db.Integer, index=True)
    duration_ms: int = db.Column(db.Integer, index=True)

    # not a foreign key so we can create and keep the log regardless of the state or process instance
    process_instance_id: int | None = db.Column(db.Integer, nullable=True, index=True)
