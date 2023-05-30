"""Message_correlation."""
from dataclasses import dataclass

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db


@dataclass
class CorrelationPropertyCache(SpiffworkflowBaseDBModel):
    """A list of known correlation properties as read from BPMN files.

    This correlation properties are not directly linked to anything
    but it provides a way to know what processes are talking about
    what messages and correlation keys.  And could be useful as an
    api endpoint if you wanted to know what another process model
    is using.
    """

    __tablename__ = "correlation_property_cache"
    id = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(50), nullable=False, index=True)
    message_name: str = db.Column(db.String(50), nullable=False, index=True)
    process_model_id: str = db.Column(db.String(255), nullable=False)
    retrieval_expression: str = db.Column(db.String(255))
