from __future__ import annotations
from spiffworkflow_backend.models.user import UserModel
from sqlalchemy import ForeignKey

from dataclasses import dataclass

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db


@dataclass
class UserPropertyModel(SpiffworkflowBaseDBModel):
    __tablename__ = "user_property"
    __table_args__ = (db.UniqueConstraint("user_id", "key", name="user_id_key_uniq"),)

    id: int = db.Column(db.Integer, primary_key=True)
    user_id: int = db.Column(ForeignKey(UserModel.id), nullable=False, index=True)  # type: ignore
    key: str = db.Column(db.String(255), nullable=False, index=True)
    value: str | None = db.Column(db.String(255))
