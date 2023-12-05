from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict

from flask import current_app
from sqlalchemy import ForeignKey
from sqlalchemy import PrimaryKeyConstraint
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.json_data import JsonDataModel  # noqa: F401
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel


class TaskDraftDataDict(TypedDict):
    process_instance_id: int
    task_definition_id_path: str
    saved_form_data_hash: str | None


@dataclass
class TaskDraftDataModel(SpiffworkflowBaseDBModel):
    __tablename__ = "task_draft_data"
    __table_args__ = (
        UniqueConstraint(
            "process_instance_id",
            "task_definition_id_path",
            name="process_instance_task_definition_unique",
        ),
        PrimaryKeyConstraint(
            "process_instance_id",
            "task_definition_id_path",
            name="process_instance_task_definition_pk",
        ),
    )

    process_instance_id: int = db.Column(ForeignKey(ProcessInstanceModel.id), nullable=False, index=True)  # type: ignore

    # a colon delimited path of bpmn_process_definition_ids for a given task
    task_definition_id_path: str = db.Column(db.String(255), nullable=False, index=True)

    saved_form_data_hash: str | None = db.Column(db.String(255), nullable=True, index=True)

    def get_saved_form_data(self) -> dict | None:
        if self.saved_form_data_hash is not None:
            return JsonDataModel.find_data_dict_by_hash(self.saved_form_data_hash)
        return None

    @classmethod
    def insert_or_update_task_draft_data_dict(cls, task_draft_data_dict: TaskDraftDataDict) -> None:
        on_duplicate_key_stmt = None
        if current_app.config["SPIFFWORKFLOW_BACKEND_DATABASE_TYPE"] == "mysql":
            insert_stmt = mysql_insert(TaskDraftDataModel).values([task_draft_data_dict])
            on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(
                saved_form_data_hash=insert_stmt.inserted.saved_form_data_hash
            )
        else:
            insert_stmt = None
            if current_app.config["SPIFFWORKFLOW_BACKEND_DATABASE_TYPE"] == "sqlite":
                insert_stmt = sqlite_insert(TaskDraftDataModel).values([task_draft_data_dict])
            else:
                insert_stmt = postgres_insert(TaskDraftDataModel).values([task_draft_data_dict])
            on_duplicate_key_stmt = insert_stmt.on_conflict_do_update(
                index_elements=["process_instance_id", "task_definition_id_path"],
                set_={"saved_form_data_hash": task_draft_data_dict["saved_form_data_hash"]},
            )
        db.session.execute(on_duplicate_key_stmt)
