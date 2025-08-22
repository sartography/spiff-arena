from __future__ import annotations

import dataclasses
import enum
import os
from dataclasses import dataclass
from dataclasses import field
from typing import Any

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

    def __hash__(self) -> Any:
        return hash(self)

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

    def to_dict(self) -> dict[str, Any]:
        """Convert the ProcessModelInfo object to a dictionary."""
        data = dataclasses.asdict(self)
        if self.files is not None:
            data["files"] = [f.serialized() for f in self.files]
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProcessModelInfo:
        """Create a ProcessModelInfo object from a dictionary."""
        data_copy = data.copy()
        if "files" in data_copy and data_copy["files"] is not None:
            data_copy["files"] = [File.from_dict(f) for f in data_copy["files"]]

        # remove keys not in dataclass
        known_fields = {f.name for f in dataclasses.fields(cls)}
        filtered_data = {k: v for k, v in data_copy.items() if k in known_fields}

        return cls(**filtered_data)

    def serialized(self) -> dict[str, Any]:
        file_objects = self.files
        dictionary = self.__dict__
        if file_objects is not None:
            serialized_files = []
            for file in file_objects:
                serialized_files.append(file.serialized())
            dictionary["files"] = serialized_files
        return dictionary

    @classmethod
    def extract_metadata(cls, task_data: dict[str, Any], metadata_extraction_paths: list[dict[str, str]]) -> dict[str, Any]:
        current_metadata = {}
        for metadata_extraction_path in metadata_extraction_paths:
            key = metadata_extraction_path["key"]
            path = metadata_extraction_path["path"]
            path_segments = path.split(".")
            data_for_key: dict[str, Any] | None = task_data
            for path_segment in path_segments:
                if path_segment in (data_for_key or {}):
                    data_for_key = (data_for_key or {})[path_segment]
                else:
                    data_for_key = None
                    break
            current_metadata[key] = data_for_key
        return current_metadata
