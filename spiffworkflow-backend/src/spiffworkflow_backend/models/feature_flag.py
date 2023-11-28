from dataclasses import dataclass

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db


@dataclass
class FeatureFlagModel(SpiffworkflowBaseDBModel):
    __tablename__ = "kkv_data_store"

    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(255), nullable=False, index=True)
    process_model_identifier: str = db.Column(db.String(255), index=True)
    top_level_keypr: str = db.Column(db.Boolean, nullable=False, index=True)
    secondary_key: str = db.Column(db.String(255), nullable=False, index=True)
    value: dict = db.Column(db.JSON, nullable=False)
    updated_at_in_seconds: int = db.Column(db.Integer, nullable=False)
    created_at_in_seconds: int = db.Column(db.Integer, nullable=False)
