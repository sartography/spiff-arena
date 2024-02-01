from dataclasses import dataclass

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db


@dataclass
class KKVDataStoreModel: #(SpiffworkflowBaseDBModel):
    __tablename__ = "kkv_data_store"

    id: int = db.Column(db.Integer, primary_key=True)
    top_level_key: str = db.Column(db.String(255), nullable=False, index=True)
    secondary_key: str = db.Column(db.String(255), nullable=False, index=True)
    value: dict = db.Column(db.JSON, nullable=False)
    updated_at_in_seconds: int = db.Column(db.Integer, nullable=False)
    created_at_in_seconds: int = db.Column(db.Integer, nullable=False)
