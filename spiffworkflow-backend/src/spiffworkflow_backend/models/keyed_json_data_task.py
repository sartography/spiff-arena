from __future__ import annotations

from spiffworkflow_backend.models.keyed_json_data import KeyedJsonDataModel
from spiffworkflow_backend.models.task import TaskModel  # noqa: F401
from sqlalchemy import ForeignKey

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db


class KeyedJsonDataTaskModel(SpiffworkflowBaseDBModel):
    __tablename__ = "keyed_json_data_task"
    __table_args__ = (
        db.UniqueConstraint(
            "keyed_json_data_hash",
            "task_guid",
            name="keyed_json_data_hash_task_guid_unique",
        ),
    )

    task_guid: str = db.Column(ForeignKey(TaskModel.guid, name="task_guid_fk"), nullable=False, index=True)
    keyed_json_data_hash: str = db.Column(
        ForeignKey(KeyedJsonDataModel.hash, name="keyed_json_data_hash_fk"), nullable=False, index=True
    )
