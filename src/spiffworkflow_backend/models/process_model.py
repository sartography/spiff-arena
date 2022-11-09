"""Process_model."""
from __future__ import annotations

import enum
from dataclasses import dataclass
from dataclasses import field
from typing import Any

import marshmallow
from marshmallow import Schema
from marshmallow.decorators import post_load

from spiffworkflow_backend.models.file import File


class NotificationType(enum.Enum):
    """NotificationType."""

    fault = "fault"
    suspend = "suspend"


@dataclass(order=True)
class ProcessModelInfo:
    """ProcessModelInfo."""

    sort_index: str = field(init=False)

    id: str
    display_name: str
    description: str
    process_group: Any | None = None
    primary_file_name: str | None = None
    primary_process_id: str | None = None
    display_order: int | None = 0
    is_review: bool = False
    files: list[File] | None = field(default_factory=list[File])
    fault_or_suspend_on_exception: str = NotificationType.fault.value
    exception_notification_addresses: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """__post_init__."""
        self.sort_index = self.id

    def __eq__(self, other: Any) -> bool:
        """__eq__."""
        if not isinstance(other, ProcessModelInfo):
            return False
        if other.id == self.id:
            return True
        return False


class ProcessModelInfoSchema(Schema):
    """ProcessModelInfoSchema."""

    class Meta:
        """Meta."""

        model = ProcessModelInfo

    id = marshmallow.fields.String(required=True)
    display_name = marshmallow.fields.String(required=True)
    description = marshmallow.fields.String()
    display_order = marshmallow.fields.Integer(allow_none=True)
    primary_file_name = marshmallow.fields.String(allow_none=True)
    primary_process_id = marshmallow.fields.String(allow_none=True)
    is_review = marshmallow.fields.Boolean(allow_none=True)
    files = marshmallow.fields.List(marshmallow.fields.Nested("FileSchema"))
    fault_or_suspend_on_exception = marshmallow.fields.String()
    exception_notification_addresses = marshmallow.fields.List(
        marshmallow.fields.String
    )

    @post_load
    def make_spec(
        self, data: dict[str, str | bool | int | NotificationType], **_: Any
    ) -> ProcessModelInfo:
        """Make_spec."""
        return ProcessModelInfo(**data)  # type: ignore
