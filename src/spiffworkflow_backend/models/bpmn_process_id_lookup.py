"""Message_model."""
from flask_bpmn.models.db import db
from flask_bpmn.models.db import SpiffworkflowBaseDBModel


class BpmnProcessIdLookup(SpiffworkflowBaseDBModel):
    """BpmnProcessIdLookup."""

    __tablename__ = "bpmn_process_id_lookup"

    id = db.Column(db.Integer, primary_key=True)
    bpmn_process_identifier = db.Column(db.String(255), unique=True, index=True)
    bpmn_file_relative_path = db.Column(db.String(255))
