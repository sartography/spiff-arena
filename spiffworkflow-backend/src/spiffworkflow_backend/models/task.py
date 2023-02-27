"""Task."""
import enum
from typing import Any
from typing import Optional
from typing import Union

import marshmallow
from marshmallow import Schema
from marshmallow_enum import EnumField  # type: ignore
from SpiffWorkflow.task import TaskStateNames  # type: ignore


class MultiInstanceType(enum.Enum):
    """MultiInstanceType."""

    none = "none"
    looping = "looping"
    parallel = "parallel"
    sequential = "sequential"


class Task:
    """Task."""

    HUMAN_TASK_TYPES = ["User Task", "Manual Task"]

    def __init__(
        self,
        id: str,
        name: str,
        title: str,
        type: str,
        state: str,
        lane: Union[str, None] = None,
        form: None = None,
        documentation: str = "",
        data: Union[dict[str, Any], None] = None,
        multi_instance_type: Union[MultiInstanceType, None] = None,
        multi_instance_count: str = "",
        multi_instance_index: str = "",
        process_identifier: str = "",
        properties: Union[dict, None] = None,
        process_instance_id: Union[int, None] = None,
        process_instance_status: Union[str, None] = None,
        process_model_display_name: Union[str, None] = None,
        process_group_identifier: Union[str, None] = None,
        process_model_identifier: Union[str, None] = None,
        form_schema: Union[dict, None] = None,
        form_ui_schema: Union[dict, None] = None,
        parent: Optional[str] = None,
        event_definition: Union[dict[str, Any], None] = None,
        call_activity_process_identifier: Optional[str] = None,
        calling_subprocess_task_id: Optional[str] = None,
        task_spiff_step: Optional[int] = None,
    ):
        """__init__."""
        self.id = id
        self.name = name
        self.title = title
        self.type = type
        self.state = state
        self.form = form
        self.documentation = documentation
        self.lane = lane
        self.parent = parent
        self.event_definition = event_definition
        self.call_activity_process_identifier = call_activity_process_identifier
        self.calling_subprocess_task_id = calling_subprocess_task_id
        self.task_spiff_step = task_spiff_step

        self.data = data
        if self.data is None:
            self.data = {}

        self.process_instance_id = process_instance_id
        self.process_instance_status = process_instance_status
        self.process_group_identifier = process_group_identifier
        self.process_model_identifier = process_model_identifier
        self.process_model_display_name = process_model_display_name
        self.form_schema = form_schema
        self.form_ui_schema = form_ui_schema

        self.multi_instance_type = (
            multi_instance_type  # Some tasks have a repeat behavior.
        )
        self.multi_instance_count = (
            multi_instance_count  # This is the number of times the task could repeat.
        )
        self.multi_instance_index = (
            multi_instance_index  # And the index of the currently repeating task.
        )
        self.process_identifier = process_identifier

        self.properties = properties  # Arbitrary extension properties from BPMN editor.
        if self.properties is None:
            self.properties = {}

    @property
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
            "form_schema": self.form_schema,
            "form_ui_schema": self.form_ui_schema,
            "parent": self.parent,
            "event_definition": self.event_definition,
            "call_activity_process_identifier": self.call_activity_process_identifier,
            "calling_subprocess_task_id": self.calling_subprocess_task_id,
            "task_spiff_step": self.task_spiff_step,
        }

    @classmethod
    def task_state_name_to_int(cls, task_state_name: str) -> int:
        task_state_integers = {v: k for k, v in TaskStateNames.items()}
        task_state_int: int = task_state_integers[task_state_name]
        return task_state_int


class OptionSchema(Schema):
    """OptionSchema."""

    class Meta:
        """Meta."""

        fields = ["id", "name", "data"]


class ValidationSchema(Schema):
    """ValidationSchema."""

    class Meta:
        """Meta."""

        fields = ["name", "config"]


class FormFieldPropertySchema(Schema):
    """FormFieldPropertySchema."""

    class Meta:
        """Meta."""

        fields = ["id", "value"]


class FormFieldSchema(Schema):
    """FormFieldSchema."""

    class Meta:
        """Meta."""

        fields = [
            "id",
            "type",
            "label",
            "default_value",
            "options",
            "validation",
            "properties",
            "value",
        ]

    default_value = marshmallow.fields.String(required=False, allow_none=True)
    options = marshmallow.fields.List(marshmallow.fields.Nested(OptionSchema))
    validation = marshmallow.fields.List(marshmallow.fields.Nested(ValidationSchema))
    properties = marshmallow.fields.List(
        marshmallow.fields.Nested(FormFieldPropertySchema)
    )


# class FormSchema(Schema):
#     """FormSchema."""
#
#     key = marshmallow.fields.String(required=True, allow_none=False)
#     fields = marshmallow.fields.List(marshmallow.fields.Nested(FormFieldSchema))


class TaskSchema(Schema):
    """TaskSchema."""

    class Meta:
        """Meta."""

        fields = [
            "id",
            "name",
            "title",
            "type",
            "state",
            "lane",
            "form",
            "documentation",
            "data",
            "multi_instance_type",
            "multi_instance_count",
            "multi_instance_index",
            "process_identifier",
            "properties",
            "process_instance_id",
            "form_schema",
            "form_ui_schema",
            "event_definition",
        ]

    multi_instance_type = EnumField(MultiInstanceType)
    documentation = marshmallow.fields.String(required=False, allow_none=True)
    # form = marshmallow.fields.Nested(FormSchema, required=False, allow_none=True)
    title = marshmallow.fields.String(required=False, allow_none=True)
    process_identifier = marshmallow.fields.String(required=False, allow_none=True)
    lane = marshmallow.fields.String(required=False, allow_none=True)

    @marshmallow.post_load
    def make_task(self, data: dict[str, Any], **kwargs: dict) -> Task:
        """Make_task."""
        return Task(**data)
