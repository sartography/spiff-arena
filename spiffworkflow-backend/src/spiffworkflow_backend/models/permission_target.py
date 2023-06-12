import re
from dataclasses import dataclass

from sqlalchemy.orm import validates

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db


class InvalidPermissionTargetUriError(Exception):
    pass


@dataclass
class PermissionTargetModel(SpiffworkflowBaseDBModel):
    URI_ALL = "/%"

    __tablename__ = "permission_target"

    id: int = db.Column(db.Integer, primary_key=True)
    uri: str = db.Column(db.String(255), unique=True, nullable=False)

    def __init__(self, uri: str, id: int | None = None):
        if id:
            self.id = id
        uri_with_percent = re.sub(r"\*", "%", uri)
        self.uri = uri_with_percent

    @validates("uri")
    def validate_uri(self, key: str, value: str) -> str:
        if re.search(r"%.", value):
            raise InvalidPermissionTargetUriError(f"Wildcard must appear at end: {value}")
        return value
