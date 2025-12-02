from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from flask import current_app
from sqlalchemy import ForeignKey
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import relationship

from spiffworkflow_backend.models.bpmn_process_definition import BpmnProcessDefinitionModel
from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db


@dataclass
class TaskDefinitionModel(SpiffworkflowBaseDBModel):
    __tablename__ = "task_definition"
    __table_args__ = (
        UniqueConstraint(
            "bpmn_process_definition_id",
            "bpmn_identifier",
            name="task_definition_unique",
        ),
    )

    id: int = db.Column(db.Integer, primary_key=True)
    bpmn_process_definition_id: int = db.Column(
        ForeignKey(BpmnProcessDefinitionModel.id),  # type: ignore
        nullable=False,
        index=True,
    )
    bpmn_process_definition = relationship(BpmnProcessDefinitionModel)

    bpmn_identifier: str = db.Column(db.String(255), nullable=False, index=True)
    bpmn_name: str | None = db.Column(db.String(255), nullable=True, index=True)
    typename: str = db.Column(db.String(255), nullable=False, index=True)

    properties_json: dict = db.Column(db.JSON, nullable=False)

    updated_at_in_seconds: int = db.Column(db.Integer)
    created_at_in_seconds: int = db.Column(db.Integer)

    @classmethod
    def insert_or_update_record(cls, task_definition_dict: dict) -> Any:
        if current_app.config["SPIFFWORKFLOW_BACKEND_DATABASE_TYPE"] == "mysql":
            # For MySQL, use naive insert to avoid deadlocks from ON DUPLICATE KEY UPDATE.
            try:
                result = db.session.execute(mysql_insert(TaskDefinitionModel).values(task_definition_dict))
                return result
            except IntegrityError as e:
                # Check if it's a duplicate key error (errno 1062)
                if e.orig.args[0] == 1062:
                    # Record already exists, return None to signal no insert occurred
                    return None
                # Some other integrity error, re-raise
                raise
        else:
            # PostgreSQL's on_conflict_do_nothing doesn't have deadlock issues
            insert_stmt = postgres_insert(TaskDefinitionModel).values(task_definition_dict)
            on_duplicate_key_stmt = insert_stmt.on_conflict_do_nothing(
                index_elements=["bpmn_process_definition_id", "bpmn_identifier"]
            )
            return db.session.execute(on_duplicate_key_stmt)

    def is_human_task(self) -> bool:
        return self.typename in ["UserTask", "ManualTask", "NoneTask"]
