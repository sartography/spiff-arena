from dataclasses import dataclass
from typing import Any
from sqlalchemy.orm import validates

from flask_marshmallow import Schema  # type: ignore
from marshmallow import INCLUDE
from sqlalchemy import UniqueConstraint
from spiffworkflow_backend.helpers.spiff_enum import SpiffEnum

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db


# SpecReferenceNotFoundError
class ReferenceNotFoundError(Exception):
    pass


class ReferenceType(SpiffEnum):
    decision = "decision"
    process = "process"
    data_store = "data_store"


# SpecReference
@dataclass()
class Reference:
    """File Reference Information.

    Includes items such as the process id and name for a BPMN,
    or the Decision id and Decision name for a DMN file.  There may be more than
    one reference that points to a particular file - if for instance, there are
    three executable processes in a collaboration within a BPMN Diagram.
    """

    identifier: str  # The id of the process or decision.  "Process_1234"
    display_name: str  # The name of the process or decision. "Invoice Submission"
    relative_location: str
    type: str  # can be 'process' or 'decision'
    file_name: str  # The name of the file where this process or decision is defined.
    relative_path: str  # The path to the file.
    messages: dict  # Any messages defined in the same file where this process is defined.
    correlations: dict  # Any correlations defined in the same file with this process.
    start_messages: list  # The names of any messages that would start this process.
    called_element_ids: list  # The element ids of any called elements

    properties: dict
    # has_lanes: bool  # If this is a process, whether it has lanes or not.
    # is_executable: bool  # Whether this process or decision is designated as executable.
    # is_primary: bool  # Whether this is the primary process of a process model

# SpecReferenceCache
class ReferenceCacheModel(SpiffworkflowBaseDBModel):
    """A cache of information about all the Processes and Decisions defined in all files."""

    __tablename__ = "reference_cache"
    __table_args__ = (UniqueConstraint("identifier", "relative_location", "type", name="reference_cache_uniq"),)

    id: int = db.Column(db.Integer, primary_key=True)
    identifier: str = db.Column(db.String(255), index=True, nullable=False)
    display_name: str = db.Column(db.String(255), index=True, nullable=False)
    type: str = db.Column(db.String(255), index=True, nullable=False)
    file_name: str = db.Column(db.String(255), nullable=False)

    # relative to SPIFFWORKFLOW_BACKEND_BPMN_SPEC_ABSOLUTE_DIR
    relative_location: str = db.Column(db.String(255), index=True, nullable=False)

    properties: dict | None = db.Column(db.JSON)
    # has_lanes = db.Column(db.Boolean())
    # is_executable = db.Column(db.Boolean())
    # is_primary = db.Column(db.Boolean())

    @classmethod
    def from_spec_reference(cls, ref: Reference) -> "ReferenceCacheModel":
        return cls(
            identifier=ref.identifier,
            display_name=ref.display_name,
            relative_location=ref.relative_location,
            type=ref.type,
            file_name=ref.file_name,
            relative_path=ref.relative_path,

            properties=ref.properties,
            # has_lanes=ref.has_lanes,
            # is_executable=ref.is_executable,
            # is_primary=ref.is_primary,
        )

    @validates("type")
    def validate_event_type(self, key: str, value: Any) -> Any:
        return self.validate_enum_field(key, value, ReferenceType)


# SpecReferenceSchema
class ReferenceSchema(Schema):  # type: ignore
    class Meta:
        model = Reference
        fields = [
            "identifier",
            "display_name",
            "process_group_id",
            "relative_location",
            "type",
            "file_name",
            "has_lanes",
            "is_executable",
            "is_primary",
        ]
        unknown = INCLUDE

