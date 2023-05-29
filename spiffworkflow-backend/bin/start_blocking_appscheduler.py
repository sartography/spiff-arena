"""Start the appscheduler in blocking mode."""
import time

from apscheduler.schedulers.background import BlockingScheduler  # type: ignore
from spiffworkflow_backend import create_app
from spiffworkflow_backend import start_scheduler
from spiffworkflow_backend.helpers.db_helper import try_to_connect


def main() -> None:
    """Main."""
    app = create_app()
    start_time = time.time()
    with app.app_context():
        try_to_connect(start_time)

    start_scheduler(app, BlockingScheduler)


if __name__ == "__main__":
    main()
