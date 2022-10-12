"""PermissionTarget."""
import re

from flask_bpmn.models.db import db
from flask_bpmn.models.db import SpiffworkflowBaseDBModel
from sqlalchemy.orm import validates


class InvalidPermissionTargetUriError(Exception):
    """InvalidPermissionTargetUriError."""


class PermissionTargetModel(SpiffworkflowBaseDBModel):
    """PermissionTargetModel."""

    __tablename__ = "permission_target"

    id = db.Column(db.Integer, primary_key=True)
    uri = db.Column(db.String(255), unique=True, nullable=False)

    @validates("uri")
    def validate_uri(self, key: str, value: str) -> str:
        """Validate_uri."""
        if re.search(r"%.", value):
            raise InvalidPermissionTargetUriError(
                f"Wildcard must appear at end: {value}"
            )
        return value
