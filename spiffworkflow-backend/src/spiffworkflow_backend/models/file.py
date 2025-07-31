from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from typing import Any

from spiffworkflow_backend.helpers.spiff_enum import SpiffEnum
from spiffworkflow_backend.models.reference_cache import Reference


class FileType(SpiffEnum):
    bpmn = "bpmn"
    css = "css"
    js = "js"
    csv = "csv"
    dmn = "dmn"
    doc = "doc"
    docx = "docx"
    gif = "gif"
    jpg = "jpg"
    json = "json"
    md = "md"
    pdf = "pdf"
    png = "png"
    ppt = "ppt"
    pptx = "pptx"
    rtf = "rtf"
    sql = "sql"
    svg = "svg"
    svg_xml = "svg+xml"
    txt = "txt"
    xls = "xls"
    xlsx = "xlsx"
    xml = "xml"
    zip = "zip"


CONTENT_TYPES = {
    "bpmn": "text/xml",
    "css": "text/css",
    "csv": "text/csv",
    "js": "application/javascript",
    "dmn": "text/xml",
    "doc": "application/msword",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "gif": "image/gif",
    "jpg": "image/jpeg",
    "json": "application/json",
    "md": "text/plain",
    "pdf": "application/pdf",
    "png": "image/png",
    "ppt": "application/vnd.ms-powerpoint",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "rtf": "application/rtf",
    "sql": "text/plain",
    "svg": "image/svg+xml",
    "svg_xml": "image/svg+xml",
    "txt": "text/plain",
    "xls": "application/vnd.ms-excel",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "xml": "application/xml",
    "zip": "application/zip",
}


@dataclass(order=True)
class File:
    sort_index: str = field(init=False)

    content_type: str
    name: str
    type: str
    last_modified: datetime
    size: int
    references: list[Reference] | None = None
    file_contents: bytes | None = None
    process_model_id: str | None = None
    bpmn_process_ids: list[str] | None = None
    file_contents_hash: str | None = None

    def __post_init__(self) -> None:
        self.sort_index = f"{self.type}:{self.name}"

    @classmethod
    def from_file_system(
        cls,
        file_name: str,
        file_type: FileType,
        content_type: str,
        last_modified: datetime,
        file_size: int,
    ) -> File:
        instance = cls(
            name=file_name,
            content_type=content_type,
            type=file_type.value,
            last_modified=last_modified,
            size=file_size,
        )
        return instance

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> File:
        """Create a File object from a dictionary."""
        data_copy = data.copy()
        data_copy["last_modified"] = datetime.fromisoformat(data_copy["last_modified"])
        if "file_contents" in data_copy and data_copy["file_contents"] is not None:
            data_copy["file_contents"] = data_copy["file_contents"].encode("utf-8")
        if "references" in data_copy and data_copy["references"] is not None:
            data_copy["references"] = [Reference.from_dict(r) for r in data_copy["references"]]

        # remove keys not in dataclass
        known_fields = {f.name for f in dataclasses.fields(cls)}
        filtered_data = {k: v for k, v in data_copy.items() if k in known_fields}

        return cls(**filtered_data)

    def serialized(self) -> dict[str, Any]:
        dictionary = self.__dict__
        if isinstance(self.file_contents, bytes):
            dictionary["file_contents"] = self.file_contents.decode("utf-8")
        return dictionary
