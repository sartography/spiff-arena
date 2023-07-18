"""Start the appscheduler in blocking mode."""
import time

from apscheduler.schedulers.background import BlockingScheduler  # type: ignore
from spiffworkflow_backend import create_app
from spiffworkflow_backend import start_scheduler
from spiffworkflow_backend.data_migrations.version_1_3 import VersionOneThree
from spiffworkflow_backend.helpers.db_helper import try_to_connect


def main() -> None:
    seconds_to_wait = 300
    print(f"sleeping for {seconds_to_wait} seconds to give the api container time to run the migration")
    time.sleep(seconds_to_wait)
    print("done sleeping")

    print("running data migration from background processor")
    app = create_app()
    start_time = time.time()

    with app.app_context():
        try_to_connect(start_time)
        VersionOneThree().run()

    end_time = time.time()
    print(
        f"done running data migration from background processor. took {end_time - start_time} seconds. starting"
        " scheduler"
    )
    start_scheduler(app, BlockingScheduler)


if __name__ == "__main__":
    main()
