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
    process_instance_migrated = "process_instance_migrated"
    process_instance_resumed = "process_instance_resumed"
    process_instance_rewound_to_task = "process_instance_rewound_to_task"
    process_instance_suspended = "process_instance_suspended"
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
    task_guid: str | None = db.Column(db.String(36), nullable=True, index=True)
    process_instance_id: int = db.Column(ForeignKey("process_instance.id"), nullable=False, index=True)

    event_type: str = db.Column(db.String(50), nullable=False, index=True)
    timestamp: float = db.Column(db.DECIMAL(17, 6), nullable=False, index=True)

    user_id = db.Column(ForeignKey(UserModel.id), nullable=True, index=True)  # type: ignore

    error_details = relationship("ProcessInstanceErrorDetailModel", back_populates="process_instance_event", cascade="delete")  # type: ignore

    @validates("event_type")
    def validate_event_type(self, key: str, value: Any) -> Any:
        return self.validate_enum_field(key, value, ProcessInstanceEventType)

    def loggable_event(self):
        return {
            "task_id": self.task_guid,
            "process_instance_id": self.process_instance_id,
            "event_type": self.event_type,
            "user_id": self.user_id,
        }
