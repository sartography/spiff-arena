from __future__ import annotations

import enum
from dataclasses import dataclass
from dataclasses import field
from typing import TYPE_CHECKING
from typing import Any

from SpiffWorkflow.util.task import TaskState  # type: ignore
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from spiffworkflow_backend.models.bpmn_process import BpmnProcessModel
from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.json_data import JsonDataModel
from spiffworkflow_backend.models.task_definition import TaskDefinitionModel

if TYPE_CHECKING:
    from spiffworkflow_backend.models.human_task_user import HumanTaskModel  # noqa: F401


class TaskNotFoundError(Exception):
    pass


class MultiInstanceType(enum.Enum):
    none = "none"
    looping = "looping"
    parallel = "parallel"
    sequential = "sequential"


# properties_json attributes:
#   "id": "a56e1403-2838-4f03-a31f-f99afe16f38d",
#   "parent": null,
#   "children": [
#     "af6ba340-71e7-46d7-b2d4-e3db1751785d"
#   ],
#   "last_state_change": 1677775475.18116,
#   "state": 32,
#   "task_spec": "Start",
#   "triggered": false,
#   "workflow_name": "Process_category_number_one_call_activity_call_activity_test_bd2e724",
#   "internal_data": {},
@dataclass
class TaskModel(SpiffworkflowBaseDBModel):
    __tablename__ = "task"
    __allow_unmapped__ = True
    guid: str = db.Column(db.String(36), nullable=False, index=True, primary_key=True, unique=True)
    bpmn_process_id: int = db.Column(ForeignKey(BpmnProcessModel.id), nullable=False, index=True)  # type: ignore
    bpmn_process = relationship(BpmnProcessModel, back_populates="tasks")
    human_tasks = relationship("HumanTaskModel", back_populates="task_model", cascade="delete")
    process_instance_id: int = db.Column(ForeignKey("process_instance.id"), nullable=False, index=True)

    # find this by looking up the "workflow_name" and "task_spec" from the properties_json
    task_definition_id: int = db.Column(ForeignKey(TaskDefinitionModel.id), nullable=False, index=True)  # type: ignore
    task_definition = relationship("TaskDefinitionModel")

    state: str = db.Column(db.String(10), nullable=False, index=True)
    properties_json: dict = db.Column(db.JSON, nullable=False)

    json_data_hash: str = db.Column(db.String(255), nullable=False, index=True)
    python_env_data_hash: str = db.Column(db.String(255), nullable=False, index=True)

    runtime_info: dict | None = db.Column(db.JSON)
    start_in_seconds: float | None = db.Column(db.DECIMAL(17, 6))
    end_in_seconds: float | None = db.Column(db.DECIMAL(17, 6))

    data: dict | None = None
    saved_form_data: dict | None = None

    # these are here to be compatible with task api
    form_schema: dict | None = None
    form_ui_schema: dict | None = None
    process_model_display_name: str | None = None
    process_model_identifier: str | None = None
    typename: str | None = None
    can_complete: bool | None = None
    extensions: dict | None = None
    name_for_display: str | None = None
    signal_buttons: list[dict] | None = None

    def get_data(self) -> dict:
        return {**self.python_env_data(), **self.json_data()}

    def python_env_data(self) -> dict:
        return JsonDataModel.find_data_dict_by_hash(self.python_env_data_hash)

    def json_data(self) -> dict:
        return JsonDataModel.find_data_dict_by_hash(self.json_data_hash)

    def parent_guid(self) -> str | None:
        if "parent" not in self.properties_json:
            return None
        parent_guid: str = self.properties_json["parent"]
        return parent_guid

    def parent_task_model(self) -> TaskModel | None:
        task_model: TaskModel = self.__class__.query.filter_by(guid=self.parent_guid()).first()
        return task_model

    @classmethod
    def sort_by_last_state_changed(cls, task_models: list[TaskModel]) -> list[TaskModel]:
        def sort_function(task: TaskModel) -> float:
            state_change: float = task.properties_json["last_state_change"]
            return state_change

        return sorted(task_models, key=sort_function)

    # this will redirect to login if the task does not allow guest access.
    # so if you already completed the task, and you are not signed in, you will get sent to a login page.
    def allows_guest(self, process_instance_id: int) -> bool:
        properties_json = self.task_definition.properties_json
        if (
            "extensions" in properties_json
            and "allowGuest" in properties_json["extensions"]
            and properties_json["extensions"]["allowGuest"] == "true"
            and self.process_instance_id == int(process_instance_id)
            and self.state != "COMPLETED"
        ):
            return True
        return False

    @classmethod
    def task_guid_allows_guest(cls, task_guid: str, process_instance_id: int) -> bool:
        task_model = cls.query.filter_by(guid=task_guid).first()
        if task_model is not None and task_model.allows_guest(process_instance_id):
            return True
        return False


@dataclass
class Task:
    HUMAN_TASK_TYPES = ["User Task", "Manual Task"]
    id: str
    name: str
    title: str
    type: str
    state: str
    can_complete: bool
    lane: str | None = None
    form: None = None
    documentation: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    multi_instance_type: MultiInstanceType | None = None
    multi_instance_count: str = ""
    multi_instance_index: str = ""
    process_identifier: str = ""
    properties: dict = field(default_factory=dict)
    runtime_info: dict | None = None
    process_instance_id: int | None = None
    process_instance_status: str | None = None
    process_model_display_name: str | None = None
    process_group_identifier: str | None = None
    process_model_identifier: str | None = None
    bpmn_process_identifier: str | None = None
    form_schema: dict | None = None
    form_ui_schema: dict | None = None
    parent: str | None = None
    event_definition: dict[str, Any] | None = None
    error_message: str | None = None
    assigned_user_group_identifier: str | None = None
    potential_owner_usernames: str | None = None
    process_model_uses_queued_execution: bool | None = None

    def serialized(self) -> dict[str, Any]:
        """Return object data in serializeable format."""
        multi_instance_type = None
        if self.multi_instance_type:
            MultiInstanceType(self.multi_instance_type)

        return {
            "id": self.id,
            "name": self.name,
            "title": self.title,
            "type": self.type,
            "state": self.state,
            "lane": self.lane,
            "can_complete": self.can_complete,
            "form": self.form,
            "documentation": self.documentation,
            "data": self.data,
            "multi_instance_type": multi_instance_type,
            "multi_instance_count": self.multi_instance_count,
            "multi_instance_index": self.multi_instance_index,
            "process_identifier": self.process_identifier,
            "properties": self.properties,
            "process_instance_id": self.process_instance_id,
            "process_instance_status": self.process_instance_status,
            "process_model_display_name": self.process_model_display_name,
            "process_group_identifier": self.process_group_identifier,
            "process_model_identifier": self.process_model_identifier,
            "bpmn_process_identifier": self.bpmn_process_identifier,
            "form_schema": self.form_schema,
            "form_ui_schema": self.form_ui_schema,
            "parent": self.parent,
            "event_definition": self.event_definition,
            "error_message": self.error_message,
            "assigned_user_group_identifier": self.assigned_user_group_identifier,
            "potential_owner_usernames": self.potential_owner_usernames,
            "process_model_uses_queued_execution": self.process_model_uses_queued_execution,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Task:
        data_copy = data.copy()
        multi_instance_type = data_copy.get("multi_instance_type")
        if multi_instance_type:
            data_copy["multi_instance_type"] = MultiInstanceType(multi_instance_type)
        else:
            data_copy["multi_instance_type"] = None
        return cls(**data_copy)

    @classmethod
    def task_state_name_to_int(cls, task_state_name: str) -> int:
        state_value: int = TaskState.get_value(task_state_name)
        return state_value


@dataclass
class Option:
    id: str
    name: str
    data: Any

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "data": self.data}

    @classmethod
    def from_dict(cls, data: dict) -> Option:
        return cls(**data)


@dataclass
class Validation:
    name: str
    config: Any

    def to_dict(self) -> dict:
        return {"name": self.name, "config": self.config}

    @classmethod
    def from_dict(cls, data: dict) -> Validation:
        return cls(**data)


@dataclass
class FormFieldProperty:
    id: str
    value: Any

    def to_dict(self) -> dict:
        return {"id": self.id, "value": self.value}

    @classmethod
    def from_dict(cls, data: dict) -> FormFieldProperty:
        return cls(**data)


@dataclass
class FormField:
    id: str
    type: str
    label: str
    options: list[Option]
    validation: list[Validation]
    properties: list[FormFieldProperty]
    default_value: str | None = None
    value: Any | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "label": self.label,
            "default_value": self.default_value,
            "options": [o.to_dict() for o in self.options],
            "validation": [v.to_dict() for v in self.validation],
            "properties": [p.to_dict() for p in self.properties],
            "value": self.value,
        }

    @classmethod
    def from_dict(cls, data: dict) -> FormField:
        return cls(
            id=data["id"],
            type=data["type"],
            label=data["label"],
            default_value=data.get("default_value"),
            options=[Option.from_dict(o) for o in data.get("options", [])],
            validation=[Validation.from_dict(v) for v in data.get("validation", [])],
            properties=[FormFieldProperty.from_dict(p) for p in data.get("properties", [])],
            value=data.get("value"),
        )
