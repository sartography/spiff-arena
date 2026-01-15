import glob
import hashlib
import os
import time
from typing import Any

from flask import current_app

from spiffworkflow_backend.data_migrations.data_migration_base import DataMigrationBase
from spiffworkflow_backend.data_migrations.version_2 import Version2
from spiffworkflow_backend.data_migrations.version_3 import Version3
from spiffworkflow_backend.data_migrations.version_4 import Version4
from spiffworkflow_backend.data_migrations.version_5 import Version5
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel


class DataMigrationFilesNotFoundError(Exception):
    pass


# simple decorator to time the func
# https://stackoverflow.com/a/11151365/6090676, thank you
def benchmark_log_func(func: Any) -> Any:
    """
    decorator to calculate the total time of a func
    """

    def st_func(*args: list, **kwargs: dict) -> Any:
        t1 = time.time()
        r = func(*args, **kwargs)
        t2 = time.time()
        class_name = args[1].__name__  # type: ignore
        # __qualname__, i know you use it every day. but if not, it's the function name prefixed with any qualifying class names
        current_app.logger.debug(f"Function={func.__qualname__}({class_name}), Time={t2 - t1}")
        return r

    return st_func


class ProcessInstanceMigrator:
    @classmethod
    def run(cls, process_instance: ProcessInstanceModel) -> bool:
        """This updates the serialization of an instance to the current expected state.

        We do not run the migrator in cases where we do not expect to update the spiff internal state,
        such as the process instance show page (where we do instantiate a processor).
        Someday, we might need to run the migrator in more places, if using spiff to read depends on
        an updated serialization.
        """

        ran_migration = False

        # if the serializer version is None, then we are dealing with a new process instance,
        # so we do not need to run the migrator
        # it will be set the newest serializer version momentarily.
        if process_instance.spiff_serializer_version is None:
            return ran_migration

        # we need to run version3 first to get the typenames in place otherwise version2 fails
        # to properly create a bpmn_process_instance when calling from_dict on the assembled dictionary
        if process_instance.spiff_serializer_version < Version2.version():
            cls.run_version(Version3, process_instance)
            cls.run_version(Version2, process_instance)
            cls.run_version(Version4, process_instance)
            ran_migration = True
        elif process_instance.spiff_serializer_version < Version3.version():
            cls.run_version(Version3, process_instance)
            cls.run_version(Version4, process_instance)
            ran_migration = True
        elif process_instance.spiff_serializer_version < Version4.version():
            cls.run_version(Version4, process_instance)
            cls.run_version(Version5, process_instance)
            ran_migration = True
        elif process_instance.spiff_serializer_version < Version5.version():
            cls.run_version(Version5, process_instance)
            ran_migration = True

        return ran_migration

    @classmethod
    @benchmark_log_func
    def run_version(cls, data_migration_version_class: DataMigrationBase, process_instance: ProcessInstanceModel) -> None:
        if process_instance.spiff_serializer_version < data_migration_version_class.version():
            data_migration_version_class.run(process_instance)
            process_instance.spiff_serializer_version = data_migration_version_class.version()
            db.session.add(process_instance)
            db.session.commit()

    @classmethod
    def get_migration_files(cls) -> list[str]:
        file_glob = os.path.join(current_app.instance_path, "..", "spiffworkflow_backend", "data_migrations", "version_*.py")
        files = sorted(glob.glob(file_glob))
        if len(files) == 0:
            raise DataMigrationFilesNotFoundError(f"Could not find data migration with expected glob: {file_glob}")
        return files

    # modified from https://gist.github.com/vinovator/d864555d9e82d25e52fd
    @classmethod
    def generate_md5_for_file(cls, file: str, chunk_size: int = 4096) -> str:
        """
        Function which takes a file name and returns md5 checksum of the file
        """
        hash = hashlib.md5()  # noqa: S324
        with open(file, "rb") as f:
            # Read the 1st block of the file
            chunk = f.read(chunk_size)
            # Keep reading the file until the end and update hash
            while chunk:
                hash.update(chunk)
                chunk = f.read(chunk_size)

        # Return the hex checksum
        return hash.hexdigest()

    @classmethod
    def generate_migration_checksum(cls) -> dict[str, str]:
        files = cls.get_migration_files()
        md5checksums = {}
        for file in files:
            md5checksum = cls.generate_md5_for_file(file)
            md5checksums[os.path.basename(file)] = md5checksum
        return md5checksums
