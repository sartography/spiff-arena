import time
from dataclasses import dataclass
from typing import Any

from flask import current_app
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import validates

from spiffworkflow_backend.helpers.spiff_enum import SpiffEnum
from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db


class FutureTaskStatus(SpiffEnum):
    waiting = "waiting"
    queued = "queued"
    completed = "completed"


@dataclass
class FutureTaskModel(SpiffworkflowBaseDBModel):
    __tablename__ = "future_task"

    guid: str = db.Column(db.String(36), primary_key=True)
    run_at_in_seconds: int = db.Column(db.Integer, nullable=False)

    # waiting, queued, complete / delete it
    status: str = db.Column(db.String(50), index=True, nullable=False, default="waiting")

    updated_at_in_seconds: int = db.Column(db.Integer, nullable=False)

    @validates("status")
    def validate_status(self, key: str, value: Any) -> Any:
        return self.validate_enum_field(key, value, FutureTaskStatus)

    @classmethod
    def insert_or_update(cls, guid: str, run_at_in_seconds: int) -> None:
        task_info = [
            {
                "guid": guid,
                "run_at_in_seconds": run_at_in_seconds,
                "updated_at_in_seconds": round(time.time()),
            }
        ]
        on_duplicate_key_stmt = None
        if current_app.config["SPIFFWORKFLOW_BACKEND_DATABASE_TYPE"] == "mysql":
            insert_stmt = mysql_insert(FutureTaskModel).values(task_info)
            on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(
                run_at_in_seconds=insert_stmt.inserted.run_at_in_seconds, updated_at_in_seconds=round(time.time())
            )
        else:
            insert_stmt = None
            if current_app.config["SPIFFWORKFLOW_BACKEND_DATABASE_TYPE"] == "sqlite":
                insert_stmt = sqlite_insert(FutureTaskModel).values(task_info)
            else:
                insert_stmt = postgres_insert(FutureTaskModel).values(task_info)
            on_duplicate_key_stmt = insert_stmt.on_conflict_do_update(
                index_elements=["guid"],
                set_={"run_at_in_seconds": run_at_in_seconds, "updated_at_in_seconds": round(time.time())},
            )
        db.session.execute(on_duplicate_key_stmt)
