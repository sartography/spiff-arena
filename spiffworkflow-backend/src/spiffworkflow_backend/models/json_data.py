from __future__ import annotations

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel


class JsonDataModel(SpiffworkflowBaseDBModel):
    __tablename__ = "json_data"
    id: int = db.Column(db.Integer, primary_key=True)

    # this is a sha256 hash of spec and serializer_version
    hash: str = db.Column(db.String(255), nullable=False, index=True, unique=True)
    data: dict = db.Column(db.JSON, nullable=False)
