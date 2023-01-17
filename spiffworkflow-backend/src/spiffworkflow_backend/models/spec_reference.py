"""Message_model."""
from dataclasses import dataclass

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel

from flask_marshmallow import Schema  # type: ignore
from marshmallow import INCLUDE
from sqlalchemy import UniqueConstraint


class SpecReferenceNotFoundError(Exception):
    """SpecReferenceNotFoundError."""


@dataclass()
class SpecReference:
    """File Reference Information.

    Includes items such as the process id and name for a BPMN,
    or the Decision id and Decision name for a DMN file.  There may be more than
    one reference that points to a particular file - if for instance, there are
    three executable processes in a collaboration within a BPMN Diagram.
    """

    identifier: str  # The id of the process or decision.  "Process_1234"
    display_name: str  # The name of the process or decision. "Invoice Submission"
    process_model_id: str
    type: str  # can be 'process' or 'decision'
    file_name: str  # The name of the file where this process or decision is defined.
    relative_path: str  # The path to the file.
    has_lanes: bool  # If this is a process, whether it has lanes or not.
    is_executable: bool  # Whether this process or decision is designated as executable.
    is_primary: bool  # Whether this is the primary process of a process model
    messages: dict  # Any messages defined in the same file where this process is defined.
    correlations: dict  # Any correlations defined in the same file with this process.
    start_messages: list  # The names of any messages that would start this process.


class SpecReferenceCache(SpiffworkflowBaseDBModel):
    """A cache of information about all the Processes and Decisions defined in all files."""

    __tablename__ = "spec_reference_cache"
    __table_args__ = (
        UniqueConstraint("identifier", "type", name="_identifier_type_unique"),
    )
    id = db.Column(db.Integer, primary_key=True)
    identifier = db.Column(db.String(255), index=True)
    display_name = db.Column(db.String(255), index=True)
    process_model_id = db.Column(db.String(255))
    type = db.Column(db.String(255), index=True)  # either 'process' or 'decision'
    file_name = db.Column(db.String(255))
    relative_path = db.Column(db.String(255))
    has_lanes = db.Column(db.Boolean())
    is_executable = db.Column(db.Boolean())
    is_primary = db.Column(db.Boolean())

    @classmethod
    def from_spec_reference(cls, ref: SpecReference) -> "SpecReferenceCache":
        """From_spec_reference."""
        return cls(
            identifier=ref.identifier,
            display_name=ref.display_name,
            process_model_id=ref.process_model_id,
            type=ref.type,
            file_name=ref.file_name,
            has_lanes=ref.has_lanes,
            is_executable=ref.is_executable,
            is_primary=ref.is_primary,
            relative_path=ref.relative_path,
        )


class SpecReferenceSchema(Schema):  # type: ignore
    """FileSchema."""

    class Meta:
        """Meta."""

        model = SpecReference
        fields = [
            "identifier",
            "display_name",
            "process_group_id",
            "process_model_id",
            "type",
            "file_name",
            "has_lanes",
            "is_executable",
            "is_primary",
        ]
        unknown = INCLUDE
