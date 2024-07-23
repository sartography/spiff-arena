from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from flask import g
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from spiffworkflow_backend.interfaces import PotentialOwnerIdList
from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.task import Task
from spiffworkflow_backend.models.task import TaskModel
from spiffworkflow_backend.models.user import UserModel

if TYPE_CHECKING:
    from spiffworkflow_backend.models.human_task_user import HumanTaskUserModel  # noqa: F401


@dataclass
class HumanTaskModel(SpiffworkflowBaseDBModel):
    __tablename__ = "human_task"

    id: int = db.Column(db.Integer, primary_key=True)
    process_instance_id: int = db.Column(ForeignKey(ProcessInstanceModel.id), nullable=False, index=True)  # type: ignore
    lane_assignment_id: int | None = db.Column(ForeignKey(GroupModel.id), index=True)
    completed_by_user_id: int = db.Column(ForeignKey(UserModel.id), nullable=True, index=True)  # type: ignore

    completed_by_user = relationship("UserModel", foreign_keys=[completed_by_user_id], viewonly=True)

    actual_owner_id: int = db.Column(ForeignKey(UserModel.id), index=True)  # type: ignore
    # actual_owner: RelationshipProperty[UserModel] = relationship(UserModel)

    form_file_name: str | None = db.Column(db.String(255))
    ui_form_file_name: str | None = db.Column(db.String(255))

    updated_at_in_seconds: int = db.Column(db.Integer)
    created_at_in_seconds: int = db.Column(db.Integer)

    task_guid: str = db.Column(ForeignKey(TaskModel.guid), nullable=True, index=True)
    task_model = relationship(TaskModel)

    task_id: str = db.Column(db.String(50))
    task_name: str = db.Column(db.String(255))
    task_title: str = db.Column(db.String(50))
    task_type: str = db.Column(db.String(50))
    task_status: str = db.Column(db.String(50))
    process_model_display_name: str = db.Column(db.String(255))
    bpmn_process_identifier: str = db.Column(db.String(255))
    completed: bool = db.Column(db.Boolean, default=False, nullable=False, index=True)

    human_task_users = relationship("HumanTaskUserModel", cascade="delete")
    potential_owners = relationship(  # type: ignore
        "UserModel",
        viewonly=True,
        secondary="human_task_user",
        overlaps="human_task_user,users",
        order_by="HumanTaskUserModel.id",
    )

    def update_attributes_from_spiff_task(self, spiff_task: SpiffTask, potential_owner_hash: PotentialOwnerIdList) -> None:
        # currently only used for process instance migrations where only the bpmn_name is allowed to be updated
        self.task_title = spiff_task.task_spec.bpmn_name
        self.lane_assignment_id = potential_owner_hash["lane_assignment_id"]

    @classmethod
    def to_task(cls, task: HumanTaskModel) -> Task:
        can_complete = False
        for user in task.human_task_users:
            if user.user_id == g.user.id:
                can_complete = True
                break

        new_task = Task(
            task.task_guid,
            task.task_name,
            task.task_title,
            task.task_type,
            task.task_status,
            can_complete,
            process_instance_id=task.process_instance_id,
        )
        if hasattr(task, "process_model_display_name"):
            new_task.process_model_display_name = task.process_model_display_name
        if hasattr(task, "process_group_identifier"):
            new_task.process_group_identifier = task.process_group_identifier
        if hasattr(task, "bpmn_process_identifier"):
            new_task.bpmn_process_identifier = task.bpmn_process_identifier

        # human tasks only have status when getting the list on the home page
        # and it comes from the process_instance. it should not be confused with task_status.
        if hasattr(task, "status"):
            new_task.process_instance_status = task.status

        return new_task
