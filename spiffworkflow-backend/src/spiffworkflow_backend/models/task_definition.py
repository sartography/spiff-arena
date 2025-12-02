from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import ForeignKey
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import relationship

from spiffworkflow_backend.models.bpmn_process_definition import BpmnProcessDefinitionModel
from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.utils.db_utils import insert_or_ignore_duplicate


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
        return insert_or_ignore_duplicate(
            model_class=TaskDefinitionModel,
            values=task_definition_dict,
            postgres_conflict_index_elements=["bpmn_process_definition_id", "bpmn_identifier"],
        )

    def is_human_task(self) -> bool:
        return self.typename in ["UserTask", "ManualTask", "NoneTask"]
