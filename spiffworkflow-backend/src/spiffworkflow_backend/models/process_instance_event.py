from __future__ import annotations

from typing import Any

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import validates

from spiffworkflow_backend.helpers.spiff_enum import SpiffEnum
from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.user import UserModel


# event types take the form [SUBJECT]_[PAST_TENSE_VERB] since subject is not always the same.
class ProcessInstanceEventType(SpiffEnum):
    process_instance_error = "process_instance_error"
    process_instance_force_run = "process_instance_force_run"
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


class ProcessInstanceEventModel(SpiffworkflowBaseDBModel):
    __tablename__ = "process_instance_event"
    id: int = db.Column(db.Integer, primary_key=True)

    # use task guid so we can bulk insert without worrying about whether or not the task has an id yet
    task_guid: str | None = db.Column(
        ForeignKey("task.guid", ondelete="CASCADE", name="process_instance_event_task_guid_fk"), nullable=True, index=True
    )
    process_instance_id: int = db.Column(ForeignKey("process_instance.id"), nullable=False, index=True)

    event_type: str = db.Column(db.String(50), nullable=False, index=True)
    timestamp: float = db.Column(db.DECIMAL(17, 6), nullable=False, index=True)

    user_id = db.Column(ForeignKey(UserModel.id), nullable=True, index=True)  # type: ignore

    error_details = relationship("ProcessInstanceErrorDetailModel", back_populates="process_instance_event", cascade="delete")  # type: ignore
    task = relationship("TaskModel")  # type: ignore

    @validates("event_type")
    def validate_event_type(self, key: str, value: Any) -> Any:
        return self.validate_enum_field(key, value, ProcessInstanceEventType)
