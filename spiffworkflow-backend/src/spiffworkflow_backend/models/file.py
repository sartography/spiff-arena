from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from dataclasses import field
from datetime import datetime
from typing import Optional

from spiffworkflow_backend.helpers.spiff_enum import SpiffEnum
from spiffworkflow_backend.models.spec_reference import SpecReference


class FileType(SpiffEnum):
    """FileType."""

    bpmn = "bpmn"
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
    svg = "svg"
    svg_xml = "svg+xml"
    txt = "txt"
    xls = "xls"
    xlsx = "xlsx"
    xml = "xml"
    zip = "zip"


CONTENT_TYPES = {
    "bpmn": "text/xml",
    "csv": "text/csv",
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
    """File."""

    sort_index: str = field(init=False)

    content_type: str
    name: str
    type: str
    last_modified: datetime
    size: int
    references: Optional[list[SpecReference]] = None
    file_contents: Optional[bytes] = None
    process_model_id: Optional[str] = None
    file_contents_hash: Optional[str] = None

    def __post_init__(self) -> None:
        """__post_init__."""
        self.sort_index = f"{self.type}:{self.name}"

    @classmethod
    def from_file_system(
        cls,
        file_name: str,
        file_type: FileType,
        content_type: str,
        last_modified: datetime,
        file_size: int,
    ) -> "File":
        """From_file_system."""
        instance = cls(
            name=file_name,
            content_type=content_type,
            type=file_type.value,
            last_modified=last_modified,
            size=file_size,
        )
        return instance

    @property
    def serialized(self) -> dict[str, Any]:
        dictionary = self.__dict__
        if isinstance(self.file_contents, bytes):
            dictionary['file_contents'] = self.file_contents.decode('utf-8')
        return dictionary
