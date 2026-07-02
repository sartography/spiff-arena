from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import ForeignKey
from sqlalchemy import UniqueConstraint

from spiffworkflow_backend.models.bpmn_process_definition import BpmnProcessDefinitionModel
from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.utils.db_utils import insert_or_ignore_duplicate


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

    @classmethod
    def insert_or_update_record(cls, parent_id: int, child_id: int) -> None:
        insert_or_ignore_duplicate(
            model_class=BpmnProcessDefinitionRelationshipModel,
            values={
                "bpmn_process_definition_parent_id": parent_id,
                "bpmn_process_definition_child_id": child_id,
            },
            postgres_conflict_index_elements=[
                "bpmn_process_definition_parent_id",
                "bpmn_process_definition_child_id",
            ],
        )
