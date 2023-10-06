import time

from spiffworkflow_backend import create_app
from spiffworkflow_backend.data_migrations.version_1_3 import VersionOneThree
from spiffworkflow_backend.data_migrations.version_2 import Version2
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from sqlalchemy import update


def main() -> None:
    start_time = time.time()
    app = create_app()
    end_time = time.time()
    print(
        f"data_migrations/run_all::create_app took {end_time - start_time} seconds"
    )
    start_time = time.time()

    with app.app_context():
        old_busted_serializer_version = '1.0-spiffworkflow-backend'
        update_query = update(ProcessInstanceModel).where(ProcessInstanceModel.spiff_serializer_version == old_busted_serializer_version).values(spiff_serializer_version='1')
        db.session.execute(update_query)
        db.session.commit()
        process_instances = ProcessInstanceModel.query.filter(ProcessInstanceModel.spiff_serializer_version < "2", ProcessInstanceModel.status.in_(ProcessInstanceModel.non_terminal_statuses())).all()
        Version2.run(process_instances)
        VersionOneThree().run()

    end_time = time.time()
    print(
        f"done running data migration from ./bin/data_migrations/version_1_3.py. took {end_time - start_time} seconds"
    )


if __name__ == "__main__":
    main()
