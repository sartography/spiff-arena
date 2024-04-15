import os
from dataclasses import dataclass

from flask import current_app
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.mysql import LONGBLOB

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel

PROCESS_INSTANCE_DATA_FILE_ON_FILE_SYSTEM = "contents:in:filesystem"


@dataclass
class ProcessInstanceFileDataModel(SpiffworkflowBaseDBModel):
    __tablename__ = "process_instance_file_data"

    id: int = db.Column(db.Integer, primary_key=True)
    process_instance_id: int = db.Column(ForeignKey(ProcessInstanceModel.id), nullable=False, index=True)  # type: ignore
    mimetype: str = db.Column(db.String(255), nullable=False)
    filename: str = db.Column(db.String(255), nullable=False)
    # this is not deferred because there is no reason to query this model if you do not want the contents
    contents: bytes = db.Column(db.LargeBinary().with_variant(LONGBLOB, "mysql"), nullable=False)
    digest: str = db.Column(db.String(64), nullable=False, index=True)
    updated_at_in_seconds: int = db.Column(db.Integer, nullable=False)
    created_at_in_seconds: int = db.Column(db.Integer, nullable=False)

    def store_file_on_file_system(self) -> None:
        filename = self.digest
        filepath = os.path.join(current_app.config["SPIFFWORKFLOW_BACKEND_PROCESS_INSTANCE_FILE_DATA_FILESYSTEM_PATH"], filename)
        with open(filepath, "w") as f:
            f.write(self.contents.decode("utf-8"))
        self.contents = PROCESS_INSTANCE_DATA_FILE_ON_FILE_SYSTEM.encode()

    def get_contents_on_file_system(self) -> bytes:
        filename = self.digest
        filepath = os.path.join(current_app.config["SPIFFWORKFLOW_BACKEND_PROCESS_INSTANCE_FILE_DATA_FILESYSTEM_PATH"], filename)
        with open(filepath) as f:
            return f.read().encode()
