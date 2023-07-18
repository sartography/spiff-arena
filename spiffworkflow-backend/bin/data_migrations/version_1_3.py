import time

from spiffworkflow_backend import create_app
from spiffworkflow_backend.data_migrations.version_1_3 import VersionOneThree


def main() -> None:
    app = create_app()
    start_time = time.time()

    with app.app_context():
        VersionOneThree().run()

    end_time = time.time()
    print(
        f"done running data migration from ./bin/data_migrations/version_1_3.py. took {end_time - start_time} seconds"
    )


if __name__ == "__main__":
    main()
