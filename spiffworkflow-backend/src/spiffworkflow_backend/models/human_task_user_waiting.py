from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.human_task import HumanTaskModel


@dataclass
class HumanTaskUserWaitingModel(SpiffworkflowBaseDBModel):
    """Stores pending human task assignments for users who haven't signed in yet.

    When lane_owners specifies a username/email that doesn't exist in the system,
    we store the assignment here. When the user signs in, we check this table and
    create the actual HumanTaskUserModel entries for any active (not completed) tasks.
    """

    __tablename__ = "human_task_user_waiting"

    __table_args__ = (
        db.UniqueConstraint(
            "human_task_id",
            "username",
            name="human_task_user_waiting_unique",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    human_task_id = db.Column(ForeignKey(HumanTaskModel.id), nullable=False, index=True)  # type: ignore
    username = db.Column(db.String(255), nullable=False, index=True)

    human_task = relationship(HumanTaskModel, backref="human_task_users_waiting")
