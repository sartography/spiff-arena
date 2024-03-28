from dataclasses import dataclass

from sqlalchemy import ForeignKey
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import relationship

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.kkv_data_store import KKVDataStoreModel


@dataclass
class KKVDataStoreEntryModel(SpiffworkflowBaseDBModel):
    __tablename__ = "kkv_data_store_entry"
    __table_args__ = (UniqueConstraint("kkv_data_store_id", "top_level_key", "secondary_key", name="_instance_keys_unique"),)

    id: int = db.Column(db.Integer, primary_key=True)
    kkv_data_store_id: int = db.Column(ForeignKey(KKVDataStoreModel.id), nullable=False, index=True)  # type: ignore
    top_level_key: str = db.Column(db.String(255), nullable=False, index=True)
    secondary_key: str = db.Column(db.String(255), nullable=False, index=True)
    value: dict = db.Column(db.JSON, nullable=False)
    updated_at_in_seconds: int = db.Column(db.Integer, nullable=False)
    created_at_in_seconds: int = db.Column(db.Integer, nullable=False)

    instance = relationship("KKVDataStoreModel", back_populates="entries")
