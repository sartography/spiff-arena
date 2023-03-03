from __future__ import annotations

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel


# contents of top-level attributes from spiff:
#   "subprocess_specs",
#   "spec",
#
# each subprocess will have its own row in this table.
# there is a join table to link them together: bpmn_process_definition_relationship
class BpmnProcessDefinitionModel(SpiffworkflowBaseDBModel):
    __tablename__ = "bpmn_process_definition"
    id: int = db.Column(db.Integer, primary_key=True)

    # this is a sha256 hash of spec and serializer_version
    # note that a call activity is its own row in this table, with its own hash,
    # and therefore it only gets stored once per version, and can be reused
    # by multiple calling processes.
    hash: str = db.Column(db.String(255), nullable=False, index=True, unique=True)

    bpmn_identifier: str = db.Column(db.String(255), nullable=False, index=True)

    properties_json: dict = db.Column(db.JSON, nullable=False)

    # process or subprocess
    # FIXME: will probably ignore for now since we do not strictly need it
    # make this nullable false and index it once we actually start using it
    type: str = db.Column(db.String(32), nullable=True)

    # TODO: remove these from process_instance
    bpmn_version_control_type: str = db.Column(db.String(50))
    bpmn_version_control_identifier: str = db.Column(db.String(255))
