from dataclasses import dataclass

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db


@dataclass
class ConfigurationModel(SpiffworkflowBaseDBModel):
    __tablename__ = "configuration"

    id: int = db.Column(db.Integer, primary_key=True)
    category: str = db.Column(db.String(255), index=True)
    value: dict = db.Column(db.JSON)
    updated_at_in_seconds: int = db.Column(db.Integer)
    created_at_in_seconds: int = db.Column(db.Integer)
