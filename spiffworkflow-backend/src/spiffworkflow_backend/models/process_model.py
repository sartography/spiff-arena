from __future__ import annotations

import enum
import os
from dataclasses import dataclass
from dataclasses import field
from typing import Any

import marshmallow
from marshmallow import Schema
from marshmallow.decorators import post_load

from spiffworkflow_backend.interfaces import ProcessGroupLite
from spiffworkflow_backend.models.file import File

# we only want to save these items to the json file
PROCESS_MODEL_SUPPORTED_KEYS_FOR_DISK_SERIALIZATION = [
    "display_name",
    "description",
    "primary_file_name",
    "primary_process_id",
    "fault_or_suspend_on_exception",
    "exception_notification_addresses",
    "metadata_extraction_paths",
]


class NotificationType(enum.Enum):
    fault = "fault"
    suspend = "suspend"


@dataclass(order=True)
class ProcessModelInfo:
    sort_index: str = field(init=False)

    id: str
    display_name: str
    description: str
    primary_file_name: str | None = None
    primary_process_id: str | None = None
    is_executable: bool = True
    fault_or_suspend_on_exception: str = NotificationType.fault.value
    exception_notification_addresses: list[str] = field(default_factory=list)
    metadata_extraction_paths: list[dict[str, str]] | None = None

    process_group: Any | None = None
    files: list[File] | None = field(default_factory=list[File])

    # just for the API
    parent_groups: list[ProcessGroupLite] | None = None
    bpmn_version_control_identifier: str | None = None

    # TODO: delete these once they no no longer mentioned in current process_model.json files
    display_order: int | None = 0

    actions: dict | None = None

    def __post_init__(self) -> None:
        self.sort_index = self.id

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, ProcessModelInfo):
            return False
        if other.id == self.id:
            return True
        return False

    # for use with os.path.join so it can work on windows
    # NOTE: in APIs, ids should always have forward slashes, even in windows.
    # this is because we have to store ids in the database, and we want the same
    # database snapshot to work on any OS.
    def id_for_file_path(self) -> str:
        return self.id.replace("/", os.sep)

    def modified_process_model_identifier(self) -> str:
        return self.modify_process_identifier_for_path_param(self.id)

    @classmethod
    def modify_process_identifier_for_path_param(cls, identifier: str) -> str:
        if "\\" in identifier:
            raise Exception(f"Found backslash in identifier: {identifier}")

        return identifier.replace("/", ":")

    def serialized(self) -> dict[str, Any]:
        file_objects = self.files
        dictionary = self.__dict__
        if file_objects is not None:
            serialized_files = []
            for file in file_objects:
                serialized_files.append(file.serialized())
            dictionary["files"] = serialized_files
        return dictionary


class ProcessModelInfoSchema(Schema):
    class Meta:
        model = ProcessModelInfo

    id = marshmallow.fields.String(required=True)
    display_name = marshmallow.fields.String(required=True)
    description = marshmallow.fields.String()
    primary_file_name = marshmallow.fields.String(allow_none=True)
    primary_process_id = marshmallow.fields.String(allow_none=True)
    files = marshmallow.fields.List(marshmallow.fields.Nested("File"))
    fault_or_suspend_on_exception = marshmallow.fields.String()
    exception_notification_addresses = marshmallow.fields.List(marshmallow.fields.String)
    metadata_extraction_paths = marshmallow.fields.List(
        marshmallow.fields.Dict(
            keys=marshmallow.fields.Str(required=False),
            values=marshmallow.fields.Str(required=False),
            required=False,
        )
    )

    @post_load
    def make_spec(self, data: dict[str, str | bool | int | NotificationType], **_: Any) -> ProcessModelInfo:
        return ProcessModelInfo(**data)  # type: ignore
