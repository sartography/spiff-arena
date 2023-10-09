import time

from flask import current_app
from typing import Any
from spiffworkflow_backend.data_migrations.version_2 import Version2
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
        # __qualname__, i know you use it every day. but if not, it's the function name prefixed with any qualifying class names
        current_app.logger.debug(f"Function={func.__qualname__}, Time={t2 - t1}")
        return r

    return st_func


class ProcessInstanceMigrator:
    @classmethod
    @benchmark_log_func
    def run_version_2(cls, process_instance: ProcessInstanceModel) -> None:
        if process_instance.spiff_serializer_version < Version2.VERSION:
            Version2.run(process_instance)
            process_instance.spiff_serializer_version = Version2.VERSION
            db.session.add(process_instance)
            db.session.commit()

    @classmethod
    def run(cls, process_instance: ProcessInstanceModel) -> None:
        """This updates the serialization of an instance to the current expected state.

        We do not run the migrator in cases where we do not expect to update the spiff internal state,
        such as the process instance show page (where we do instantiate a processor).
        Someday, we might need to run the migrator in more places, if using spiff to read depends on
        an updated serialization.
        """
        cls.run_version_2(process_instance)
