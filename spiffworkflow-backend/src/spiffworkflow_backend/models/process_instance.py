from __future__ import annotations

from typing import Any

import marshmallow
from marshmallow import INCLUDE
from marshmallow import Schema
from marshmallow_enum import EnumField  # type: ignore
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import validates

from spiffworkflow_backend.helpers.spiff_enum import SpiffEnum
from spiffworkflow_backend.models.bpmn_process import BpmnProcessModel
from spiffworkflow_backend.models.bpmn_process_definition import BpmnProcessDefinitionModel
from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.task import Task
from spiffworkflow_backend.models.task import TaskSchema
from spiffworkflow_backend.models.user import UserModel


class ProcessInstanceNotFoundError(Exception):
    pass


class ProcessInstanceTaskDataCannotBeUpdatedError(Exception):
    pass


class ProcessInstanceCannotBeDeletedError(Exception):
    pass


class ProcessInstanceStatus(SpiffEnum):
    not_started = "not_started"
    user_input_required = "user_input_required"
    waiting = "waiting"
    complete = "complete"
    error = "error"
    suspended = "suspended"
    terminated = "terminated"


class ProcessInstanceModel(SpiffworkflowBaseDBModel):
    __tablename__ = "process_instance"
    __allow_unmapped__ = True
    id: int = db.Column(db.Integer, primary_key=True)
    process_model_identifier: str = db.Column(db.String(255), nullable=False, index=True)
    process_model_display_name: str = db.Column(db.String(255), nullable=False, index=True)
    process_initiator_id: int = db.Column(ForeignKey(UserModel.id), nullable=False, index=True)  # type: ignore
    bpmn_process_definition_id: int | None = db.Column(
        ForeignKey(BpmnProcessDefinitionModel.id), nullable=True, index=True  # type: ignore
    )
    bpmn_process_id: int | None = db.Column(ForeignKey(BpmnProcessModel.id), nullable=True, index=True)  # type: ignore

    spiff_serializer_version = db.Column(db.String(50), nullable=True)

    process_initiator = relationship("UserModel")
    bpmn_process_definition = relationship(BpmnProcessDefinitionModel)

    active_human_tasks = relationship(
        "HumanTaskModel",
        primaryjoin=(
            "and_(HumanTaskModel.process_instance_id==ProcessInstanceModel.id, HumanTaskModel.completed == False)"
        ),
    )  # type: ignore

    bpmn_process = relationship(BpmnProcessModel, cascade="delete")
    tasks = relationship("TaskModel", cascade="delete")  # type: ignore
    task_draft_data = relationship("TaskDraftDataModel", cascade="delete")  # type: ignore
    process_instance_events = relationship("ProcessInstanceEventModel", cascade="delete")  # type: ignore
    process_instance_file_data = relationship("ProcessInstanceFileDataModel", cascade="delete")  # type: ignore
    human_tasks = relationship(
        "HumanTaskModel",
        cascade="delete",
        overlaps="active_human_tasks",
    )  # type: ignore
    message_instances = relationship("MessageInstanceModel", cascade="delete")  # type: ignore
    process_metadata = relationship(
        "ProcessInstanceMetadataModel",
        cascade="delete",
    )  # type: ignore
    process_instance_queue = relationship(
        "ProcessInstanceQueueModel",
        cascade="delete",
    )  # type: ignore

    start_in_seconds: int | None = db.Column(db.Integer, index=True)
    end_in_seconds: int | None = db.Column(db.Integer, index=True)
    task_updated_at_in_seconds: int = db.Column(db.Integer, nullable=True)
    updated_at_in_seconds: int = db.Column(db.Integer)
    created_at_in_seconds: int = db.Column(db.Integer)
    status: str = db.Column(db.String(50), index=True)

    bpmn_version_control_type: str = db.Column(db.String(50))
    bpmn_version_control_identifier: str = db.Column(db.String(255))
    last_milestone_bpmn_name: str = db.Column(db.String(255))

    bpmn_xml_file_contents: str | None = None
    bpmn_xml_file_contents_retrieval_error: str | None = None
    process_model_with_diagram_identifier: str | None = None

    # full, none
    persistence_level: str = "full"

    def serialized(self) -> dict[str, Any]:
        """Return object data in serializeable format."""
        return {
            "id": self.id,
            "bpmn_version_control_identifier": self.bpmn_version_control_identifier,
            "bpmn_version_control_type": self.bpmn_version_control_type,
            "bpmn_xml_file_contents_retrieval_error": self.bpmn_xml_file_contents_retrieval_error,
            "bpmn_xml_file_contents": self.bpmn_xml_file_contents,
            "created_at_in_seconds": self.created_at_in_seconds,
            "end_in_seconds": self.end_in_seconds,
            "last_milestone_bpmn_name": self.last_milestone_bpmn_name,
            "process_initiator_id": self.process_initiator_id,
            "process_initiator_username": self.process_initiator.username,
            "process_model_display_name": self.process_model_display_name,
            "process_model_identifier": self.process_model_identifier,
            "start_in_seconds": self.start_in_seconds,
            "status": self.status,
            "task_updated_at_in_seconds": self.task_updated_at_in_seconds,
            "updated_at_in_seconds": self.updated_at_in_seconds,
        }

    def serialized_with_metadata(self) -> dict[str, Any]:
        process_instance_attributes = self.serialized()
        process_instance_attributes["process_metadata"] = self.process_metadata
        process_instance_attributes["process_model_with_diagram_identifier"] = (
            self.process_model_with_diagram_identifier
        )
        return process_instance_attributes

    @validates("status")
    def validate_status(self, key: str, value: Any) -> Any:
        return self.validate_enum_field(key, value, ProcessInstanceStatus)

    def can_submit_task(self) -> bool:
        return not self.has_terminal_status() and self.status != "suspended"

    def can_receive_message(self) -> bool:
        """If this process can currently accept messages."""
        return not self.has_terminal_status() and self.status != "suspended"

    def has_terminal_status(self) -> bool:
        return self.status in self.terminal_statuses()

    @classmethod
    def terminal_statuses(cls) -> list[str]:
        return ["complete", "error", "terminated"]

    @classmethod
    def non_terminal_statuses(cls) -> list[str]:
        terminal_status_values = cls.terminal_statuses()
        return [s for s in ProcessInstanceStatus.list() if s not in terminal_status_values]

    @classmethod
    def active_statuses(cls) -> list[str]:
        return ["not_started", "user_input_required", "waiting"]


class ProcessInstanceModelSchema(Schema):
    class Meta:
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
        return obj.status


class ProcessInstanceApi:
    def __init__(
        self,
        id: int,
        status: ProcessInstanceStatus,
        next_task: Task | None,
        process_model_identifier: str,
        process_model_display_name: str,
        updated_at_in_seconds: int,
    ) -> None:
        self.id = id
        self.status = status
        self.next_task = next_task  # The next task that requires user input.
        self.process_model_identifier = process_model_identifier
        self.process_model_display_name = process_model_display_name
        self.updated_at_in_seconds = updated_at_in_seconds


class ProcessInstanceApiSchema(Schema):
    class Meta:
        model = ProcessInstanceApi
        fields = [
            "id",
            "status",
            "next_task",
            "process_model_identifier",
            "process_model_display_name",
            "updated_at_in_seconds",
        ]
        unknown = INCLUDE

    status = EnumField(ProcessInstanceStatus)
    next_task = marshmallow.fields.Nested(TaskSchema, dump_only=True, required=False)

    @marshmallow.post_load
    def make_process_instance(self, data: dict[str, Any], **kwargs: dict) -> ProcessInstanceApi:
        keys = [
            "id",
            "status",
            "next_task",
            "process_model_identifier",
            "process_model_display_name",
            "updated_at_in_seconds",
        ]
        filtered_fields = {key: data[key] for key in keys}
        filtered_fields["next_task"] = TaskSchema().make_task(data["next_task"])
        return ProcessInstanceApi(**filtered_fields)
