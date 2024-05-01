from sqlalchemy import ForeignKey
from sqlalchemy import PrimaryKeyConstraint

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db


class ProcessCallerRelationshipModel(SpiffworkflowBaseDBModel):
    """A cache of calling process ids for all Processes defined in all files."""

    __tablename__ = "process_caller_relationship"
    __table_args__ = (
        PrimaryKeyConstraint(
            "called_reference_cache_process_id",
            "calling_reference_cache_process_id",
            name="process_caller_relationship_primary_key",
        ),
    )

    called_reference_cache_process_id = db.Column(ForeignKey("reference_cache.id"), nullable=False, index=True)
    calling_reference_cache_process_id = db.Column(ForeignKey("reference_cache.id"), nullable=False, index=True)
