from __future__ import annotations

import time
from dataclasses import dataclass

from flask import current_app
from sqlalchemy import ForeignKey
from sqlalchemy import asc

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db


@dataclass
class TaskInstructionsForEndUserModel(SpiffworkflowBaseDBModel):
    __tablename__ = "task_instructions_for_end_user"

    task_guid: str = db.Column(db.String(36), primary_key=True)
    instruction: str = db.Column(db.String(255), nullable=False)
    process_instance_id: int = db.Column(ForeignKey("process_instance.id"), nullable=False, index=True)

    # we need this to maintain order
    timestamp: float = db.Column(db.DECIMAL(17, 6), nullable=False, index=True)

    @classmethod
    def create_record(
        cls, task_guid: str, process_instance_id: int, instruction: str
    ) -> TaskInstructionsForEndUserModel:
        return TaskInstructionsForEndUserModel(
            task_guid=task_guid,
            process_instance_id=process_instance_id,
            instruction=instruction,
            timestamp=time.time(),
        )

    @classmethod
    def entries_for_process_instance(cls, process_instance_id: int) -> list[TaskInstructionsForEndUserModel]:
        entries: list[TaskInstructionsForEndUserModel] = (
            cls.query.filter_by(process_instance_id=process_instance_id)
            .order_by(asc(TaskInstructionsForEndUserModel.timestamp))  # type: ignore
            .all()
        )
        return entries

    @classmethod
    def retrieve_and_clear(cls, process_instance_id: int) -> list[dict]:
        entries = cls.entries_for_process_instance(process_instance_id)
        # convert to list[dict] here so we can remove the records from the db right after
        instructions: list[dict] = current_app.json.loads(current_app.json.dumps(entries))
        for e in entries:
            db.session.delete(e)
        db.session.commit()
        return instructions
