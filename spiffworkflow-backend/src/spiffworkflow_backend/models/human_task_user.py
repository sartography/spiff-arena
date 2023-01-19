"""Human_task_user."""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import ForeignKey

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.user import UserModel


@dataclass
class HumanTaskUserModel(SpiffworkflowBaseDBModel):
    """HumanTaskUserModel."""

    __tablename__ = "human_task_user"

    __table_args__ = (
        db.UniqueConstraint(
            "human_task_id",
            "user_id",
            name="human_task_user_unique",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    human_task_id = db.Column(
        ForeignKey(HumanTaskModel.id), nullable=False, index=True  # type: ignore
    )
    user_id = db.Column(ForeignKey(UserModel.id), nullable=False, index=True)  # type: ignore
