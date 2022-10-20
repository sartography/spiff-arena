"""Active_task."""
from __future__ import annotations

import json
from dataclasses import dataclass

from flask_bpmn.models.db import db
from flask_bpmn.models.db import SpiffworkflowBaseDBModel
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import RelationshipProperty

from spiffworkflow_backend.models.principal import PrincipalModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.task import Task


@dataclass
class ActiveTaskModel(SpiffworkflowBaseDBModel):
    """ActiveTaskModel."""

    __tablename__ = "active_task"
    __table_args__ = (
        db.UniqueConstraint(
            "task_id", "process_instance_id", name="active_task_unique"
        ),
    )

    assigned_principal: RelationshipProperty[PrincipalModel] = relationship(
        PrincipalModel
    )
    id: int = db.Column(db.Integer, primary_key=True)
    process_instance_id: int = db.Column(
        ForeignKey(ProcessInstanceModel.id), nullable=False  # type: ignore
    )
    assigned_principal_id: int = db.Column(ForeignKey(PrincipalModel.id))
    form_file_name: str | None = db.Column(db.String(50))
    ui_form_file_name: str | None = db.Column(db.String(50))

    updated_at_in_seconds: int = db.Column(db.Integer)
    created_at_in_seconds: int = db.Column(db.Integer)

    task_id = db.Column(db.String(50))
    task_name = db.Column(db.String(50))
    task_title = db.Column(db.String(50))
    task_type = db.Column(db.String(50))
    task_status = db.Column(db.String(50))
    process_model_display_name = db.Column(db.String(255))
    task_data: str = db.Column(db.Text(4294000000))

    @classmethod
    def to_task(cls, task: ActiveTaskModel) -> Task:
        """To_task."""
        task_data = json.loads(task.task_data)

        new_task = Task(
            task.task_id,
            task.task_name,
            task.task_title,
            task.task_type,
            task.task_status,
            data=task_data,
            process_instance_id=task.process_instance_id,
            process_instance_status=task.status,
        )
        if hasattr(task, "process_model_display_name"):
            new_task.process_model_display_name = task.process_model_display_name
        if hasattr(task, "process_group_identifier"):
            new_task.process_group_identifier = task.process_group_identifier
        if hasattr(task, "process_model_identifier"):
            new_task.process_model_identifier = task.process_model_identifier

        return new_task
