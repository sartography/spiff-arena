from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_instance_file_data import PROCESS_INSTANCE_DATA_FILE_ON_FILE_SYSTEM
from spiffworkflow_backend.models.process_instance_file_data import ProcessInstanceFileDataModel


class ProcessInstanceFileDataMigrator:
    @classmethod
    def migrate_from_database_to_filesystem(cls) -> None:
        file_data = ProcessInstanceFileDataModel.query.filter(
            ProcessInstanceFileDataModel.contents != PROCESS_INSTANCE_DATA_FILE_ON_FILE_SYSTEM.encode()
        ).all()

        for file in file_data:
            file.store_file_on_file_system()
            db.session.add(file)
        db.session.commit()
