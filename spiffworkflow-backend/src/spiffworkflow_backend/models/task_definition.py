from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from flask import current_app
from sqlalchemy import ForeignKey
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.dialects.postgresql import insert as postgres_insert
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
        new_stuff = {"bpmn_identifier": task_definition_dict["bpmn_identifier"]}
        on_duplicate_key_stmt = None
        if current_app.config["SPIFFWORKFLOW_BACKEND_DATABASE_TYPE"] == "mysql":
            insert_stmt = mysql_insert(TaskDefinitionModel).values(task_definition_dict)
            on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(**new_stuff)
        else:
            insert_stmt = postgres_insert(TaskDefinitionModel).values(task_definition_dict)
            on_duplicate_key_stmt = insert_stmt.on_conflict_do_nothing(
                index_elements=["bpmn_process_definition_id", "bpmn_identifier"]
            )
        return db.session.execute(on_duplicate_key_stmt)
