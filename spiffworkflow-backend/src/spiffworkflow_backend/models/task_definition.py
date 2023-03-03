from __future__ import annotations

from sqlalchemy import ForeignKey
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import relationship

from spiffworkflow_backend.models.bpmn_process_definition import (
    BpmnProcessDefinitionModel,
)
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel


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
        ForeignKey(BpmnProcessDefinitionModel.id), nullable=False
    )  # type: ignore
    bpmn_process_definition = relationship(BpmnProcessDefinitionModel)

    bpmn_identifier: str = db.Column(db.String(255), nullable=False, index=True)
    properties_json: dict = db.Column(db.JSON, nullable=False)
    typename: str = db.Column(db.String(255), nullable=False)
