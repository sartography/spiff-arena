from sqlalchemy import ForeignKey
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.mysql import LONGBLOB

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db


class ModelSourceBlobModel(SpiffworkflowBaseDBModel):
    __tablename__ = "model_source_blob"

    digest: str = db.Column(db.String(64), primary_key=True)
    contents: bytes = db.Column(db.LargeBinary().with_variant(LONGBLOB, "mysql"), nullable=False)


class ModelSourceManifestModel(SpiffworkflowBaseDBModel):
    __tablename__ = "model_source_manifest"

    digest: str = db.Column(db.String(64), primary_key=True)
    manifest: dict = db.Column(db.JSON, nullable=False)


class ModelSourceVersionModel(SpiffworkflowBaseDBModel):
    """A source version can share its compiled definition with other source versions."""

    __tablename__ = "model_source_version"
    __table_args__ = (UniqueConstraint("definition_id", "manifest_digest", name="model_source_version_unique"),)

    id: int = db.Column(db.Integer, primary_key=True)
    definition_id: int = db.Column(ForeignKey("bpmn_process_definition.id"), nullable=False, index=True)
    manifest_digest: str = db.Column(ForeignKey(ModelSourceManifestModel.digest), nullable=False, index=True)
