"""Active_task."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from flask_bpmn.models.db import db
from flask_bpmn.models.db import SpiffworkflowBaseDBModel
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import RelationshipProperty

from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.task import Task
from spiffworkflow_backend.models.user import UserModel


if TYPE_CHECKING:
    from spiffworkflow_backend.models.active_task_user import (  # noqa: F401
        ActiveTaskUserModel,
    )


@dataclass
class ActiveTaskModel(SpiffworkflowBaseDBModel):
    """ActiveTaskModel."""

    __tablename__ = "active_task"
    __table_args__ = (
        db.UniqueConstraint(
            "task_id", "process_instance_id", name="active_task_unique"
        ),
    )

    actual_owner: RelationshipProperty[UserModel] = relationship(UserModel)
    id: int = db.Column(db.Integer, primary_key=True)
    process_instance_id: int = db.Column(
        ForeignKey(ProcessInstanceModel.id), nullable=False  # type: ignore
    )
    actual_owner_id: int = db.Column(ForeignKey(UserModel.id))
    lane_assignment_id: int | None = db.Column(ForeignKey(GroupModel.id))
    form_file_name: str | None = db.Column(db.String(50))
    ui_form_file_name: str | None = db.Column(db.String(50))

    updated_at_in_seconds: int = db.Column(db.Integer)
    created_at_in_seconds: int = db.Column(db.Integer)

    task_id: str = db.Column(db.String(50))
    task_name: str = db.Column(db.String(50))
    task_title: str = db.Column(db.String(50))
    task_type: str = db.Column(db.String(50))
    task_status: str = db.Column(db.String(50))
    process_model_display_name: str = db.Column(db.String(255))

    active_task_users = relationship("ActiveTaskUserModel", cascade="delete")
    potential_owners = relationship(  # type: ignore
        "UserModel",
        viewonly=True,
        secondary="active_task_user",
        overlaps="active_task_user,users",
    )

    @classmethod
    def to_task(cls, task: ActiveTaskModel) -> Task:
        """To_task."""
        new_task = Task(
            task.task_id,
            task.task_name,
            task.task_title,
            task.task_type,
            task.task_status,
            process_instance_id=task.process_instance_id,
        )
        if hasattr(task, "process_model_display_name"):
            new_task.process_model_display_name = task.process_model_display_name
        if hasattr(task, "process_group_identifier"):
            new_task.process_group_identifier = task.process_group_identifier
        if hasattr(task, "process_model_identifier"):
            new_task.process_model_identifier = task.process_model_identifier

        # active tasks only have status when getting the list on the home page
        # and it comes from the process_instance. it should not be confused with task_status.
        if hasattr(task, "status"):
            new_task.process_instance_status = task.status

        return new_task
