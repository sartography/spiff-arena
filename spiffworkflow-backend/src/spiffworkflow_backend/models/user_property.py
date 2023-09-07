from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import ForeignKey

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.user import UserModel


@dataclass
class UserPropertyModel(SpiffworkflowBaseDBModel):
    __tablename__ = "user_property"
    __table_args__ = (db.UniqueConstraint("user_id", "key", name="user_id_key_uniq"),)

    id: int = db.Column(db.Integer, primary_key=True)
    user_id: int = db.Column(ForeignKey(UserModel.id), nullable=False, index=True)  # type: ignore
    key: str = db.Column(db.String(255), nullable=False, index=True)
    value: str | None = db.Column(db.String(255))
