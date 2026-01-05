from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.human_task import HumanTaskModel


@dataclass
class HumanTaskGroupModel(SpiffworkflowBaseDBModel):
    """Associates groups with human tasks for dynamic lane_owners group resolution.

    When lane_owners specifies a group (e.g., "group:reviewers"), the group reference
    is stored here. Users in these groups can complete the task, and this is resolved
    dynamically - so users who join the group after task creation can still complete it.
    """

    __tablename__ = "human_task_group"

    __table_args__ = (
        db.UniqueConstraint(
            "human_task_id",
            "group_id",
            name="human_task_group_unique",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    human_task_id = db.Column(ForeignKey(HumanTaskModel.id), nullable=False, index=True)  # type: ignore
    group_id = db.Column(ForeignKey(GroupModel.id), nullable=False, index=True)

    human_task = relationship(HumanTaskModel)
    group = relationship(GroupModel)
