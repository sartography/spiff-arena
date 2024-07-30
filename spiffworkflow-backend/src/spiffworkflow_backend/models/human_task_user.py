from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import validates

from spiffworkflow_backend.helpers.spiff_enum import SpiffEnum
from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.user import UserModel


class HumanTaskUserAddedBy(SpiffEnum):
    guest = "guest"
    lane_assignment = "lane_assignment"
    lane_owner = "lane_owner"
    manual = "manual"
    process_initiator = "process_initiator"


@dataclass
class HumanTaskUserModel(SpiffworkflowBaseDBModel):
    __tablename__ = "human_task_user"

    __table_args__ = (
        db.UniqueConstraint(
            "human_task_id",
            "user_id",
            name="human_task_user_unique",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    human_task_id = db.Column(ForeignKey(HumanTaskModel.id), nullable=False, index=True)  # type: ignore
    user_id = db.Column(ForeignKey(UserModel.id), nullable=False, index=True)  # type: ignore
    added_by: str = db.Column(db.String(20), index=True)

    human_task = relationship(HumanTaskModel, back_populates="human_task_users")

    @validates("added_by")
    def validate_status(self, key: str, value: Any) -> Any:
        return self.validate_enum_field(key, value, HumanTaskUserAddedBy)
