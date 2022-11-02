"""Process_instance."""
from __future__ import annotations

from dataclasses import dataclass
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
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.models.task import Task
from spiffworkflow_backend.models.task import TaskSchema
from spiffworkflow_backend.models.user import UserModel


class NavigationItemSchema(Schema):
    """NavigationItemSchema."""

    class Meta:
        """Meta."""

        fields = [
            "spec_id",
            "name",
            "spec_type",
            "task_id",
            "description",
            "backtracks",
            "indent",
            "lane",
            "state",
            "children",
        ]
        unknown = INCLUDE

    state = marshmallow.fields.String(required=False, allow_none=True)
    description = marshmallow.fields.String(required=False, allow_none=True)
    backtracks = marshmallow.fields.String(required=False, allow_none=True)
    lane = marshmallow.fields.String(required=False, allow_none=True)
    task_id = marshmallow.fields.String(required=False, allow_none=True)
    children = marshmallow.fields.List(
        marshmallow.fields.Nested(lambda: NavigationItemSchema())
    )


class ProcessInstanceStatus(SpiffEnum):
    """ProcessInstanceStatus."""

    not_started = "not_started"
    user_input_required = "user_input_required"
    waiting = "waiting"
    complete = "complete"
    faulted = "faulted"
    suspended = "suspended"
    terminated = "terminated"
    erroring = "erroring"


class ProcessInstanceModel(SpiffworkflowBaseDBModel):
    """ProcessInstanceModel."""

    __tablename__ = "process_instance"
    id: int = db.Column(db.Integer, primary_key=True)
    process_model_identifier: str = db.Column(db.String(50), nullable=False, index=True)
    process_group_identifier: str = db.Column(db.String(50), nullable=False, index=True)
    process_initiator_id: int = db.Column(ForeignKey(UserModel.id), nullable=False)
    process_initiator = relationship("UserModel")

    active_tasks = relationship("ActiveTaskModel", cascade="delete")  # type: ignore
    spiff_logs = relationship("SpiffLoggingModel", cascade="delete")  # type: ignore
    message_instances = relationship("MessageInstanceModel", cascade="delete")  # type: ignore
    message_correlations = relationship("MessageCorrelationModel", cascade="delete")  # type: ignore
    spiff_step_details = relationship("SpiffStepDetailsModel", cascade="delete")  # type: ignore

    bpmn_json: str | None = deferred(db.Column(db.JSON))  # type: ignore
    start_in_seconds: int | None = db.Column(db.Integer)
    end_in_seconds: int | None = db.Column(db.Integer)
    updated_at_in_seconds: int = db.Column(db.Integer)
    created_at_in_seconds: int = db.Column(db.Integer)
    status: str = db.Column(db.String(50))

    bpmn_xml_file_contents: bytes | None = None
    bpmn_version_control_type: str = db.Column(db.String(50))
    bpmn_version_control_identifier: str = db.Column(db.String(255))
    spiff_step: int = db.Column(db.Integer)

    @property
    def serialized(self) -> dict[str, Any]:
        """Return object data in serializeable format."""
        local_bpmn_xml_file_contents = ""
        if self.bpmn_xml_file_contents:
            local_bpmn_xml_file_contents = self.bpmn_xml_file_contents.decode("utf-8")

        return {
            "id": self.id,
            "process_model_identifier": self.process_model_identifier,
            "process_group_identifier": self.process_group_identifier,
            "status": self.status,
            "bpmn_json": self.bpmn_json,
            "start_in_seconds": self.start_in_seconds,
            "end_in_seconds": self.end_in_seconds,
            "process_initiator_id": self.process_initiator_id,
            "bpmn_xml_file_contents": local_bpmn_xml_file_contents,
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


class ProcessInstanceModelSchema(Schema):
    """ProcessInstanceModelSchema."""

    class Meta:
        """Meta."""

        model = ProcessInstanceModel
        fields = [
            "id",
            "process_model_identifier",
            "process_group_identifier",
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
        process_group_identifier: str,
        completed_tasks: int,
        updated_at_in_seconds: int,
        is_review: bool,
        title: str,
    ) -> None:
        """__init__."""
        self.id = id
        self.status = status
        self.next_task = next_task  # The next task that requires user input.
        #        self.navigation = navigation  fixme:  would be a hotness.
        self.process_model_identifier = process_model_identifier
        self.process_group_identifier = process_group_identifier
        self.completed_tasks = completed_tasks
        self.updated_at_in_seconds = updated_at_in_seconds
        self.title = title
        self.is_review = is_review


class ProcessInstanceApiSchema(Schema):
    """ProcessInstanceApiSchema."""

    class Meta:
        """Meta."""

        model = ProcessInstanceApi
        fields = [
            "id",
            "status",
            "next_task",
            "navigation",
            "process_model_identifier",
            "process_group_identifier",
            "completed_tasks",
            "updated_at_in_seconds",
            "is_review",
            "title",
            "study_id",
            "state",
        ]
        unknown = INCLUDE

    status = EnumField(ProcessInstanceStatus)
    next_task = marshmallow.fields.Nested(TaskSchema, dump_only=True, required=False)
    navigation = marshmallow.fields.List(
        marshmallow.fields.Nested(NavigationItemSchema, dump_only=True)
    )
    state = marshmallow.fields.String(allow_none=True)

    @marshmallow.post_load
    def make_process_instance(
        self, data: dict[str, Any], **kwargs: dict
    ) -> ProcessInstanceApi:
        """Make_process_instance."""
        keys = [
            "id",
            "status",
            "next_task",
            "navigation",
            "process_model_identifier",
            "process_group_identifier",
            "completed_tasks",
            "updated_at_in_seconds",
            "is_review",
            "title",
            "study_id",
            "state",
        ]
        filtered_fields = {key: data[key] for key in keys}
        filtered_fields["next_task"] = TaskSchema().make_task(data["next_task"])
        return ProcessInstanceApi(**filtered_fields)


@dataclass
class ProcessInstanceMetadata:
    """ProcessInstanceMetadata."""

    id: int
    display_name: str | None = None
    description: str | None = None
    spec_version: str | None = None
    state: str | None = None
    status: str | None = None
    completed_tasks: int | None = None
    is_review: bool | None = None
    state_message: str | None = None
    process_model_identifier: str | None = None
    process_group_id: str | None = None

    @classmethod
    def from_process_instance(
        cls, process_instance: ProcessInstanceModel, process_model: ProcessModelInfo
    ) -> ProcessInstanceMetadata:
        """From_process_instance."""
        instance = cls(
            id=process_instance.id,
            display_name=process_model.display_name,
            description=process_model.description,
            process_group_id=process_model.process_group_id,
            state_message=process_instance.state_message,
            status=process_instance.status,
            completed_tasks=process_instance.completed_tasks,
            is_review=process_model.is_review,
            process_model_identifier=process_instance.process_model_identifier,
        )
        return instance


class ProcessInstanceMetadataSchema(Schema):
    """ProcessInstanceMetadataSchema."""

    status = EnumField(ProcessInstanceStatus)

    class Meta:
        """Meta."""

        model = ProcessInstanceMetadata
        additional = [
            "id",
            "display_name",
            "description",
            "state",
            "completed_tasks",
            "process_group_id",
            "is_review",
            "state_message",
        ]
        unknown = INCLUDE
