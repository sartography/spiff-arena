import time

from flask import current_app
from spiffworkflow_backend import create_app
from spiffworkflow_backend.data_migrations.version_1_3 import VersionOneThree
from spiffworkflow_backend.data_migrations.version_2 import Version2
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from sqlalchemy import update


# simple decorator to time the func
# https://stackoverflow.com/a/11151365/6090676, thank you
def benchmark_log_func(func):
    """
    decorator to calculate the total time of a func
    """

    def st_func(*args, **kwargs):
        t1 = time.time()
        r = func(*args, **kwargs)
        t2 = time.time()
        # __qualname__, i know you use it every day. but if not, it's the function name prefixed with any qualifying class names
        current_app.logger.debug(f"Function={func.__qualname__}, Time={t2 - t1}")
        return r

    return st_func


@benchmark_log_func
def put_serializer_version_onto_numeric_track() -> None:
    old_busted_serializer_version = "1.0-spiffworkflow-backend"
    update_query = (
        update(ProcessInstanceModel)
        .where(ProcessInstanceModel.spiff_serializer_version == old_busted_serializer_version)
        .values(spiff_serializer_version="1")
    )
    db.session.execute(update_query)
    db.session.commit()


def all_potentially_relevant_process_instances() -> list[ProcessInstanceModel]:
    return ProcessInstanceModel.query.filter(
        ProcessInstanceModel.spiff_serializer_version < Version2.VERSION,
        ProcessInstanceModel.status.in_(ProcessInstanceModel.non_terminal_statuses()),
    ).all()


@benchmark_log_func
def run_version_1() -> None:
    VersionOneThree().run()  # make this a class method


@benchmark_log_func
def run_version_2(process_instances: list[ProcessInstanceModel]) -> None:
    Version2.run(process_instances)


def main() -> None:
    start_time = time.time()
    app = create_app()
    end_time = time.time()

    with app.app_context():
        current_app.logger.debug(f"data_migrations/run_all::create_app took {end_time - start_time} seconds")
        start_time = time.time()
        put_serializer_version_onto_numeric_track()
        process_instances = all_potentially_relevant_process_instances()
        potentially_relevant_instance_count = len(process_instances)
        current_app.logger.debug(
            f"Found potentially relevant process_instances: {potentially_relevant_instance_count}"
        )
        if potentially_relevant_instance_count > 0:
            run_version_1()
            # this will run while using the new per instance on demand data migration framework
            # run_version_2(process_instances)

        end_time = time.time()
        current_app.logger.debug(
            f"done running data migrations in ./bin/data_migrations/run_all.py. took {end_time - start_time} seconds"
        )


if __name__ == "__main__":
    main()
