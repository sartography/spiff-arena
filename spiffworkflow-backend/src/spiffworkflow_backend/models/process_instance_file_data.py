import os
from dataclasses import dataclass

from flask import current_app
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.mysql import LONGBLOB

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel

PROCESS_INSTANCE_DATA_FILE_ON_FILE_SYSTEM = "contents_in:filesystem"
PROCESS_INSTANCE_DATA_FILE_ON_FILE_SYSTEM_DIR_COUNT = 2


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

    def get_contents(self) -> bytes:
        file_contents = self.contents
        if current_app.config["SPIFFWORKFLOW_BACKEND_PROCESS_INSTANCE_FILE_DATA_FILESYSTEM_PATH"] is not None:
            file_contents = self.get_contents_on_file_system()
        return file_contents

    def store_file_on_file_system(self) -> None:
        filepath = self.get_full_filepath()
        try:
            os.makedirs(os.path.dirname(filepath))
        except FileExistsError:
            pass

        with open(filepath, "wb") as f:
            f.write(self.contents)
        self.contents = PROCESS_INSTANCE_DATA_FILE_ON_FILE_SYSTEM.encode()

    def get_contents_on_file_system(self) -> bytes:
        filepath = self.get_full_filepath()
        with open(filepath, "rb") as f:
            return f.read()

    def get_full_filepath(self) -> str:
        dir_parts = self.__class__.get_hashed_directory_structure(self.digest)
        return os.path.join(
            current_app.config["SPIFFWORKFLOW_BACKEND_PROCESS_INSTANCE_FILE_DATA_FILESYSTEM_PATH"], *dir_parts, self.digest
        )

    @classmethod
    def get_hashed_directory_structure(cls, digest: str) -> list[str]:
        dir_parts = []
        for ii in range(PROCESS_INSTANCE_DATA_FILE_ON_FILE_SYSTEM_DIR_COUNT):
            start_index = ii * PROCESS_INSTANCE_DATA_FILE_ON_FILE_SYSTEM_DIR_COUNT
            end_index = start_index + PROCESS_INSTANCE_DATA_FILE_ON_FILE_SYSTEM_DIR_COUNT
            dir_parts.append(digest[start_index:end_index])
        return dir_parts
