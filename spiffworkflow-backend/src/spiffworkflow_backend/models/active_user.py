from __future__ import annotations
from spiffworkflow_backend.models.user import UserModel
from sqlalchemy import ForeignKey

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel


class ActiveUserModel(SpiffworkflowBaseDBModel):
    __tablename__ = "active_user"
    __table_args__ = (db.UniqueConstraint("user_id", "last_visited_identifier", name="user_last_visited_unique"),)

    id: int = db.Column(db.Integer, primary_key=True)
    user_id: int = db.Column(ForeignKey(UserModel.id), nullable=False, index=True)  # type: ignore
    last_visited_identifier: str = db.Column(db.String(255), nullable=False, index=True)
    last_seen_in_seconds: int = db.Column(db.Integer)
