"""Active_task_user."""
from __future__ import annotations

from dataclasses import dataclass

from flask_bpmn.models.db import db
from flask_bpmn.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.active_task import ActiveTaskModel
from spiffworkflow_backend.models.user import UserModel
from sqlalchemy import ForeignKey


@dataclass
class ActiveTaskUserModel(SpiffworkflowBaseDBModel):
    """ActiveTaskUserModel."""

    __tablename__ = "active_task_user"

    __table_args__ = (
        db.UniqueConstraint(
            "active_task_id",
            "user_id",
            name="active_task_user_unique",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    active_task_id = db.Column(
        ForeignKey(ActiveTaskModel.id), nullable=False, index=True  # type: ignore
    )
    user_id = db.Column(ForeignKey(UserModel.id), nullable=False, index=True)
