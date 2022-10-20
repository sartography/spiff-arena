"""PermissionTarget."""
import re
from dataclasses import dataclass
from typing import Optional

from flask_bpmn.models.db import db
from flask_bpmn.models.db import SpiffworkflowBaseDBModel
from sqlalchemy.orm import validates


class InvalidPermissionTargetUriError(Exception):
    """InvalidPermissionTargetUriError."""


@dataclass
class PermissionTargetModel(SpiffworkflowBaseDBModel):
    """PermissionTargetModel."""

    URI_ALL = "/%"

    __tablename__ = "permission_target"

    id: int = db.Column(db.Integer, primary_key=True)
    uri: str = db.Column(db.String(255), unique=True, nullable=False)

    def __init__(self, uri: str, id: Optional[int] = None):
        """__init__."""
        if id:
            self.id = id
        uri_with_percent = re.sub(r"\*", "%", uri)
        self.uri = uri_with_percent

    @validates("uri")
    def validate_uri(self, key: str, value: str) -> str:
        """Validate_uri."""
        if re.search(r"%.", value):
            raise InvalidPermissionTargetUriError(
                f"Wildcard must appear at end: {value}"
            )
        return value
