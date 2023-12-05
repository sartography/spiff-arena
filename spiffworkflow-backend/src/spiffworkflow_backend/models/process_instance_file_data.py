from dataclasses import dataclass

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.mysql import LONGBLOB

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel


@dataclass
class ProcessInstanceFileDataModel(SpiffworkflowBaseDBModel):
    __tablename__ = "process_instance_file_data"

    id: int = db.Column(db.Integer, primary_key=True)
    process_instance_id: int = db.Column(ForeignKey(ProcessInstanceModel.id), nullable=False, index=True)  # type: ignore
    identifier: str = db.Column(db.String(255), nullable=False)
    list_index: int | None = db.Column(db.Integer, nullable=True)
    mimetype: str = db.Column(db.String(255), nullable=False)
    filename: str = db.Column(db.String(255), nullable=False)
    # this is not deferred because there is no reason to query this model if you do not want the contents
    contents: str = db.Column(db.LargeBinary().with_variant(LONGBLOB, "mysql"), nullable=False)
    digest: str = db.Column(db.String(64), nullable=False, index=True)

    updated_at_in_seconds: int = db.Column(db.Integer, nullable=False)
    created_at_in_seconds: int = db.Column(db.Integer, nullable=False)
