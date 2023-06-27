from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import ForeignKey
from sqlalchemy import UniqueConstraint

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.json_data import JsonDataModel  # noqa: F401
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel


@dataclass
class TaskDraftDataModel(SpiffworkflowBaseDBModel):
    __tablename__ = "task_draft_data"
    __table_args__ = (
        UniqueConstraint(
            "process_instance_id",
            "task_definition_id_path",
            name="process_instance_task_definition_unique",
        ),
    )

    id: int = db.Column(db.Integer, primary_key=True)
    process_instance_id: int = db.Column(
        ForeignKey(ProcessInstanceModel.id), nullable=False, index=True  # type: ignore
    )

    # a colon delimited path of bpmn_process_definition_ids for a given task
    task_definition_id_path: str = db.Column(db.String(255), nullable=False, index=True)

    saved_form_data_hash: str | None = db.Column(db.String(255), nullable=True, index=True)

    def get_saved_form_data(self) -> dict | None:
        if self.saved_form_data_hash is not None:
            return JsonDataModel.find_data_dict_by_hash(self.saved_form_data_hash)
        return None
