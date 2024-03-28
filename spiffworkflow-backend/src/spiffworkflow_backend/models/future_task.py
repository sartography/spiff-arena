import time
from dataclasses import dataclass

from flask import current_app
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.sql import false

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db


@dataclass
class FutureTaskModel(SpiffworkflowBaseDBModel):
    __tablename__ = "future_task"

    guid: str = db.Column(db.String(36), primary_key=True)
    run_at_in_seconds: int = db.Column(db.Integer, nullable=False, index=True)
    completed: bool = db.Column(db.Boolean, default=False, nullable=False, index=True)
    archived_for_process_instance_status: bool = db.Column(
        # db.Boolean, default=False, server_default=db.sql.False_(), nullable=False, index=True
        db.Boolean,
        default=False,
        server_default=false(),
        nullable=False,
        index=True,
    )

    updated_at_in_seconds: int = db.Column(db.Integer, nullable=False)

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
