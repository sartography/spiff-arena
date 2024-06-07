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
    def run(cls, process_instance: ProcessInstanceModel) -> None:
        """This updates the serialization of an instance to the current expected state.

        We do not run the migrator in cases where we do not expect to update the spiff internal state,
        such as the process instance show page (where we do instantiate a processor).
        Someday, we might need to run the migrator in more places, if using spiff to read depends on
        an updated serialization.
        """

        # if the serializer version is None, then we are dealing with a new process instance,
        # so we do not need to run the migrator
        # it will be set the newest serializer version momentarily.
        if process_instance.spiff_serializer_version is None:
            return

        # we need to run version3 first to get the typenames in place otherwise version2 fails
        # to properly create a bpmn_process_instance when calling from_dict on the assembled dictionary
        if process_instance.spiff_serializer_version < Version2.version():
            cls.run_version(Version3, process_instance)
            cls.run_version(Version2, process_instance)
            cls.run_version(Version4, process_instance)
        elif process_instance.spiff_serializer_version < Version3.version():
            cls.run_version(Version3, process_instance)
            cls.run_version(Version4, process_instance)
        elif process_instance.spiff_serializer_version < Version4.version():
            cls.run_version(Version4, process_instance)
            cls.run_version(Version5, process_instance)
        else:
            cls.run_version(Version5, process_instance)

    @classmethod
    @benchmark_log_func
    def run_version(cls, data_migration_version_class: DataMigrationBase, process_instance: ProcessInstanceModel) -> None:
        if process_instance.spiff_serializer_version < data_migration_version_class.version():
            data_migration_version_class.run(process_instance)
            process_instance.spiff_serializer_version = data_migration_version_class.version()
            db.session.add(process_instance)
            db.session.commit()
