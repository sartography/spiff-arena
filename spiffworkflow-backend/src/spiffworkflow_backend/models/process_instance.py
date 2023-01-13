"""Process_instance."""
from __future__ import annotations

from typing import Any
from typing import cast

import marshmallow
from flask_bpmn.models.db import db
from flask_bpmn.models.db import SpiffworkflowBaseDBModel
from marshmallow import INCLUDE
from marshmallow import Schema
from marshmallow_enum import EnumField  # type: ignore
from SpiffWorkflow.util.deep_merge import DeepMerge  # type: ignore
from sqlalchemy import ForeignKey
from sqlalchemy.orm import deferred
from sqlalchemy.orm import relationship
from sqlalchemy.orm import validates

from spiffworkflow_backend.helpers.spiff_enum import SpiffEnum
from spiffworkflow_backend.models.task import Task
from spiffworkflow_backend.models.task import TaskSchema
from spiffworkflow_backend.models.user import UserModel


class ProcessInstanceNotFoundError(Exception):
    """ProcessInstanceNotFoundError."""


class ProcessInstanceTaskDataCannotBeUpdatedError(Exception):
    """ProcessInstanceTaskDataCannotBeUpdatedError."""


class ProcessInstanceCannotBeDeletedError(Exception):
    """ProcessInstanceCannotBeDeletedError."""


class ProcessInstanceStatus(SpiffEnum):
    """ProcessInstanceStatus."""

    not_started = "not_started"
    user_input_required = "user_input_required"
    waiting = "waiting"
    complete = "complete"
    error = "error"
    suspended = "suspended"
    terminated = "terminated"


class ProcessInstanceModel(SpiffworkflowBaseDBModel):
    """ProcessInstanceModel."""

    __tablename__ = "process_instance"
    id: int = db.Column(db.Integer, primary_key=True)
    process_model_identifier: str = db.Column(
        db.String(255), nullable=False, index=True
    )
    process_model_display_name: str = db.Column(
        db.String(255), nullable=False, index=True
    )
    process_initiator_id: int = db.Column(ForeignKey(UserModel.id), nullable=False)  # type: ignore
    process_initiator = relationship("UserModel")

    active_human_tasks = relationship(
        "HumanTaskModel",
        primaryjoin=(
            "and_(HumanTaskModel.process_instance_id==ProcessInstanceModel.id,"
            " HumanTaskModel.completed == False)"
        ),
    )  # type: ignore

    human_tasks = relationship(
        "HumanTaskModel",
        cascade="delete",
        overlaps="active_human_tasks",
    )  # type: ignore
    message_instances = relationship("MessageInstanceModel", cascade="delete")  # type: ignore
    message_correlations = relationship("MessageCorrelationModel", cascade="delete")  # type: ignore

    bpmn_json: str | None = deferred(db.Column(db.JSON))  # type: ignore
    start_in_seconds: int | None = db.Column(db.Integer)
    end_in_seconds: int | None = db.Column(db.Integer)
    updated_at_in_seconds: int = db.Column(db.Integer)
    created_at_in_seconds: int = db.Column(db.Integer)
    status: str = db.Column(db.String(50))

    bpmn_xml_file_contents: str | None = None
    bpmn_version_control_type: str = db.Column(db.String(50))
    bpmn_version_control_identifier: str = db.Column(db.String(255))
    spiff_step: int = db.Column(db.Integer)

    @property
    def serialized(self) -> dict[str, Any]:
        """Return object data in serializeable format."""
        return {
            "id": self.id,
            "process_model_identifier": self.process_model_identifier,
            "process_model_display_name": self.process_model_display_name,
            "status": self.status,
            "start_in_seconds": self.start_in_seconds,
            "end_in_seconds": self.end_in_seconds,
            "created_at_in_seconds": self.created_at_in_seconds,
            "updated_at_in_seconds": self.updated_at_in_seconds,
            "process_initiator_id": self.process_initiator_id,
            "bpmn_xml_file_contents": self.bpmn_xml_file_contents,
            "bpmn_version_control_identifier": self.bpmn_version_control_identifier,
            "bpmn_version_control_type": self.bpmn_version_control_type,
            "spiff_step": self.spiff_step,
            "process_initiator_username": self.process_initiator.username,
        }

    @property
    def serialized_flat(self) -> dict:
        """Return object in serializeable format with data merged together with top-level attributes.

        Top-level attributes like process_model_identifier and status win over data attributes.
        """
        serialized_top_level_attributes = self.serialized
        serialized_top_level_attributes.pop("data", None)
        return cast(dict, DeepMerge.merge(self.data, serialized_top_level_attributes))

    @validates("status")
    def validate_status(self, key: str, value: Any) -> Any:
        """Validate_status."""
        return self.validate_enum_field(key, value, ProcessInstanceStatus)

    def can_submit_task(self) -> bool:
        """Can_submit_task."""
        return not self.has_terminal_status() and self.status != "suspended"

    def has_terminal_status(self) -> bool:
        """Has_terminal_status."""
        return self.status in self.terminal_statuses()

    @classmethod
    def terminal_statuses(cls) -> list[str]:
        """Terminal_statuses."""
        return ["complete", "error", "terminated"]


class ProcessInstanceModelSchema(Schema):
    """ProcessInstanceModelSchema."""

    class Meta:
        """Meta."""

        model = ProcessInstanceModel
        fields = [
            "id",
            "process_model_identifier",
            "process_model_display_name",
            "process_initiator_id",
            "start_in_seconds",
            "end_in_seconds",
            "updated_at_in_seconds",
            "created_at_in_seconds",
            "status",
            "bpmn_version_control_identifier",
        ]

    status = marshmallow.fields.Method("get_status", dump_only=True)

    def get_status(self, obj: ProcessInstanceModel) -> str:
        """Get_status."""
        return obj.status


class ProcessInstanceApi:
    """ProcessInstanceApi."""

    def __init__(
        self,
        id: int,
        status: ProcessInstanceStatus,
        next_task: Task | None,
        process_model_identifier: str,
        process_model_display_name: str,
        completed_tasks: int,
        updated_at_in_seconds: int,
    ) -> None:
        """__init__."""
        self.id = id
        self.status = status
        self.next_task = next_task  # The next task that requires user input.
        self.process_model_identifier = process_model_identifier
        self.process_model_display_name = process_model_display_name
        self.completed_tasks = completed_tasks
        self.updated_at_in_seconds = updated_at_in_seconds


class ProcessInstanceApiSchema(Schema):
    """ProcessInstanceApiSchema."""

    class Meta:
        """Meta."""

        model = ProcessInstanceApi
        fields = [
            "id",
            "status",
            "next_task",
            "process_model_identifier",
            "process_model_display_name",
            "completed_tasks",
            "updated_at_in_seconds",
        ]
        unknown = INCLUDE

    status = EnumField(ProcessInstanceStatus)
    next_task = marshmallow.fields.Nested(TaskSchema, dump_only=True, required=False)

    @marshmallow.post_load
    def make_process_instance(
        self, data: dict[str, Any], **kwargs: dict
    ) -> ProcessInstanceApi:
        """Make_process_instance."""
        keys = [
            "id",
            "status",
            "next_task",
            "process_model_identifier",
            "process_model_display_name",
            "completed_tasks",
            "updated_at_in_seconds",
        ]
        filtered_fields = {key: data[key] for key in keys}
        filtered_fields["next_task"] = TaskSchema().make_task(data["next_task"])
        return ProcessInstanceApi(**filtered_fields)
