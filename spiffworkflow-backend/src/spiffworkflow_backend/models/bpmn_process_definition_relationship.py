from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import ForeignKey
from sqlalchemy import UniqueConstraint

from spiffworkflow_backend.models.bpmn_process_definition import BpmnProcessDefinitionModel
from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db


@dataclass
class BpmnProcessDefinitionRelationshipModel(SpiffworkflowBaseDBModel):
    __tablename__ = "bpmn_process_definition_relationship"
    __table_args__ = (
        UniqueConstraint(
            "bpmn_process_definition_parent_id",
            "bpmn_process_definition_child_id",
            name="bpmn_process_definition_relationship_unique",
        ),
    )

    id: int = db.Column(db.Integer, primary_key=True)
    bpmn_process_definition_parent_id: int = db.Column(
        ForeignKey(BpmnProcessDefinitionModel.id),  # type: ignore
        nullable=False,
        index=True,
    )
    bpmn_process_definition_child_id: int = db.Column(
        ForeignKey(BpmnProcessDefinitionModel.id),  # type: ignore
        nullable=False,
        index=True,
    )
