from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import validates

from spiffworkflow_backend.helpers.spiff_enum import SpiffEnum
from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.task import TaskModel  # noqa: F401
from spiffworkflow_backend.models.user import UserModel


# event types take the form [SUBJECT]_[PAST_TENSE_VERB] since subject is not always the same.
class ProcessInstanceEventType(SpiffEnum):
    process_instance_created = "process_instance_created"
    process_instance_completed = "process_instance_completed"
    process_instance_error = "process_instance_error"
    process_instance_force_run = "process_instance_force_run"
    process_instance_migrated = "process_instance_migrated"
    process_instance_resumed = "process_instance_resumed"
    process_instance_rewound_to_task = "process_instance_rewound_to_task"
    process_instance_suspended = "process_instance_suspended"
    process_instance_suspended_for_error = "process_instance_suspended_for_error"
    process_instance_terminated = "process_instance_terminated"
    task_cancelled = "task_cancelled"
    task_completed = "task_completed"
    task_data_edited = "task_data_edited"
    task_executed_manually = "task_executed_manually"
    task_failed = "task_failed"
    task_skipped = "task_skipped"


@dataclass
class ProcessInstanceEventModel(SpiffworkflowBaseDBModel):
    __tablename__ = "process_instance_event"
    id: int = db.Column(db.Integer, primary_key=True)

    # use task guid so we can bulk insert without worrying about whether or not the task has an id yet
    # we considered putting a foreign key constraint on this in july 2024, and decided not to mostly
    # because it was scary. it would also delete events on reset and migrate, which felt less than ideal.
    task_guid: str | None = db.Column(db.String(36), nullable=True, index=True)
    process_instance_id: int = db.Column(ForeignKey("process_instance.id"), nullable=False, index=True)

    event_type: str = db.Column(db.String(50), nullable=False, index=True)
    timestamp: float = db.Column(db.DECIMAL(17, 6), nullable=False, index=True)

    user_id = db.Column(ForeignKey(UserModel.id), nullable=True, index=True)  # type: ignore
    user = relationship("UserModel", foreign_keys=[user_id])

    error_details = relationship("ProcessInstanceErrorDetailModel", back_populates="process_instance_event", cascade="delete")  # type: ignore
    migration_details = relationship(
        "ProcessInstanceMigrationDetailModel", back_populates="process_instance_event", cascade="delete"
    )  # type: ignore

    def task(self) -> TaskModel | None:
        task_model: TaskModel | None = TaskModel.query.filter_by(guid=self.task_guid).first()
        return task_model

    @validates("event_type")
    def validate_event_type(self, key: str, value: Any) -> Any:
        return self.validate_enum_field(key, value, ProcessInstanceEventType)
