from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db


# TODO: delete this file
class ProcessCallerCacheModel(SpiffworkflowBaseDBModel):
    """A cache of calling process ids for all Processes defined in all files."""

    __tablename__ = "process_caller_cache"
    id = db.Column(db.Integer, primary_key=True)
    process_identifier = db.Column(db.String(255), index=True)
    calling_process_identifier = db.Column(db.String(255))
