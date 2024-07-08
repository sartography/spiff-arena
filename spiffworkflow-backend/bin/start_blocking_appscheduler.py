"""Start the appscheduler in blocking mode."""

import time

from apscheduler.schedulers.background import BlockingScheduler  # type: ignore
from spiffworkflow_backend import create_app
from spiffworkflow_backend.background_processing.apscheduler import start_apscheduler


def main() -> None:
    # TODO: in 30 days remove this sleep when the new bash wrapper script is on prod envs
    seconds_to_wait = 100
    print(f"sleeping for {seconds_to_wait} seconds to give the api container time to run the migration")
    time.sleep(seconds_to_wait)
    print("done sleeping")
    ####

    app = create_app()
    start_apscheduler(app, BlockingScheduler)


if __name__ == "__main__":
    main()
