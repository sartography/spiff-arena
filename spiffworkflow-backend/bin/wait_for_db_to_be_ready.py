"""Wait for db to be ready."""

import time

from spiffworkflow_backend import create_app
from spiffworkflow_backend.helpers.db_helper import try_to_connect


def main() -> None:
    app = create_app()
    start_time = time.time()
    with app.app_context():
        try_to_connect(start_time)


if __name__ == "__main__":
    main()
