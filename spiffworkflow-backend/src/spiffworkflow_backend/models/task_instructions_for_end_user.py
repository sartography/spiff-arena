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
    instruction_template: str | None = db.Column(db.Text(), nullable=True)
    task_data: dict | None = db.Column(db.JSON, nullable=True)
    process_model_identifier: str | None = db.Column(db.String(255), nullable=True)
    bpmn_file_name: str | None = db.Column(db.String(255), nullable=True)
    bpmn_process_identifier: str | None = db.Column(db.String(255), nullable=True)
    task_bpmn_identifier: str | None = db.Column(db.String(255), nullable=True)
    source_artifact_ref: dict[str, str] | None = db.Column(db.JSON, nullable=True)
    bpmn_version_control_identifier: str | None = db.Column(db.String(255), nullable=True)
    process_instance_id: int = db.Column(ForeignKey("process_instance.id"), nullable=False, index=True)
    has_been_retrieved: bool = db.Column(db.Boolean, nullable=False, default=False, index=True)

    # we need this to maintain order
    timestamp: float = db.Column(db.DECIMAL(17, 6), nullable=False, index=True)

    @classmethod
    def insert_or_update_record(
        cls,
        task_guid: str,
        process_instance_id: int,
        instruction: str,
        *,
        instruction_template: str | None = None,
        task_data: dict | None = None,
        process_model_identifier: str | None = None,
        bpmn_file_name: str | None = None,
        bpmn_process_identifier: str | None = None,
        task_bpmn_identifier: str | None = None,
        source_artifact_ref: dict[str, str] | None = None,
        bpmn_version_control_identifier: str | None = None,
    ) -> None:
        record = [
            {
                "task_guid": task_guid,
                "process_instance_id": process_instance_id,
                "instruction": instruction,
                "instruction_template": instruction_template,
                "task_data": task_data,
                "process_model_identifier": process_model_identifier,
                "bpmn_file_name": bpmn_file_name,
                "bpmn_process_identifier": bpmn_process_identifier,
                "task_bpmn_identifier": task_bpmn_identifier,
                "source_artifact_ref": source_artifact_ref,
                "bpmn_version_control_identifier": bpmn_version_control_identifier,
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
