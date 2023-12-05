from __future__ import annotations

import time
from dataclasses import dataclass

from flask import current_app
from sqlalchemy import ForeignKey
from sqlalchemy import desc
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.dialects.postgresql import insert as postgres_insert

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db


@dataclass
class TaskInstructionsForEndUserModel(SpiffworkflowBaseDBModel):
    __tablename__ = "task_instructions_for_end_user"

    task_guid: str = db.Column(db.String(36), primary_key=True)
    instruction: str = db.Column(db.Text(), nullable=False)
    process_instance_id: int = db.Column(ForeignKey("process_instance.id"), nullable=False, index=True)
    has_been_retrieved: bool = db.Column(db.Boolean, nullable=False, default=False, index=True)

    # we need this to maintain order
    timestamp: float = db.Column(db.DECIMAL(17, 6), nullable=False, index=True)

    @classmethod
    def insert_or_update_record(cls, task_guid: str, process_instance_id: int, instruction: str) -> None:
        record = [
            {
                "task_guid": task_guid,
                "process_instance_id": process_instance_id,
                "instruction": instruction,
                "timestamp": time.time(),
            }
        ]
        on_duplicate_key_stmt = None
        if current_app.config["SPIFFWORKFLOW_BACKEND_DATABASE_TYPE"] == "mysql":
            insert_stmt = mysql_insert(TaskInstructionsForEndUserModel).values(record)
            on_duplicate_key_stmt = insert_stmt.prefix_with("IGNORE")
            # on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(instruction=insert_stmt.inserted.instruction)
        else:
            insert_stmt = postgres_insert(TaskInstructionsForEndUserModel).values(record)
            on_duplicate_key_stmt = insert_stmt.on_conflict_do_nothing(index_elements=["task_guid"])
        db.session.execute(on_duplicate_key_stmt)

    @classmethod
    def entries_for_process_instance(cls, process_instance_id: int) -> list[TaskInstructionsForEndUserModel]:
        entries: list[TaskInstructionsForEndUserModel] = (
            cls.query.filter_by(process_instance_id=process_instance_id, has_been_retrieved=False)
            .order_by(desc(TaskInstructionsForEndUserModel.timestamp))  # type: ignore
            .all()
        )
        return entries

    @classmethod
    def retrieve_and_clear(cls, process_instance_id: int) -> list[TaskInstructionsForEndUserModel]:
        entries = cls.entries_for_process_instance(process_instance_id)
        # convert to list[dict] here so we can remove the records from the db right after
        for e in entries:
            e.has_been_retrieved = True
            db.session.add(e)
        db.session.commit()
        return entries
