"""Start the appscheduler in blocking mode."""

from apscheduler.schedulers.background import BlockingScheduler  # type: ignore

from spiffworkflow_backend import create_app
from spiffworkflow_backend.background_processing.apscheduler import start_apscheduler


def main() -> None:
    app = create_app()
    start_apscheduler(app.app, BlockingScheduler)


if __name__ == "__main__":
    main()
