from dataclasses import dataclass
from typing import TYPE_CHECKING

from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import relationship

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db

if TYPE_CHECKING:
    from spiffworkflow_backend.models.kkv_data_store_entry import KKVDataStoreEntryModel  # noqa: F401


@dataclass
class KKVDataStoreModel(SpiffworkflowBaseDBModel):
    __tablename__ = "kkv_data_store"
    __table_args__ = (UniqueConstraint("identifier", "location", name="_kkv_identifier_location_unique"),)

    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(255), index=True, nullable=False)
    identifier: str = db.Column(db.String(255), index=True, nullable=False)
    location: str = db.Column(db.String(255), nullable=False)
    schema: dict = db.Column(db.JSON, nullable=False)
    description: str = db.Column(db.String(255))
    updated_at_in_seconds: int = db.Column(db.Integer, nullable=False)
    created_at_in_seconds: int = db.Column(db.Integer, nullable=False)

    entries = relationship("KKVDataStoreEntryModel", cascade="delete")
