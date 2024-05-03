from flask import current_app
from sqlalchemy import ForeignKey
from sqlalchemy import PrimaryKeyConstraint
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.dialects.postgresql import insert as postgres_insert

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db


class CalledProcessNotFoundError(Exception):
    pass


class CallingProcessNotFoundError(Exception):
    pass


class ProcessCallerRelationshipModel(SpiffworkflowBaseDBModel):
    """A cache of calling process ids for all Processes defined in all files."""

    __tablename__ = "process_caller_relationship"
    __table_args__ = (
        PrimaryKeyConstraint(
            "called_reference_cache_process_id",
            "calling_reference_cache_process_id",
            name="process_caller_relationship_pk",
        ),
    )

    called_reference_cache_process_id = db.Column(
        ForeignKey("reference_cache.id", name="called_reference_cache_process_id_fk"), nullable=False, index=True
    )
    calling_reference_cache_process_id = db.Column(
        ForeignKey("reference_cache.id", name="calling_reference_cache_process_id_fk"), nullable=False, index=True
    )

    @classmethod
    def insert_or_update(cls, called_reference_cache_process_id: int, calling_reference_cache_process_id: int) -> None:
        caller_info = {
            "called_reference_cache_process_id": called_reference_cache_process_id,
            "calling_reference_cache_process_id": calling_reference_cache_process_id,
        }
        on_duplicate_key_stmt = None
        if current_app.config["SPIFFWORKFLOW_BACKEND_DATABASE_TYPE"] == "mysql":
            insert_stmt = mysql_insert(ProcessCallerRelationshipModel).values(caller_info)
            # We don't actually want to update anything but it doesn't really matter if we do since it should be the same value
            on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(
                called_reference_cache_process_id=insert_stmt.inserted.called_reference_cache_process_id
            )
        else:
            insert_stmt = postgres_insert(ProcessCallerRelationshipModel).values(caller_info)
            on_duplicate_key_stmt = insert_stmt.on_conflict_do_nothing(
                index_elements=["called_reference_cache_process_id", "calling_reference_cache_process_id"]
            )
        db.session.execute(on_duplicate_key_stmt)
