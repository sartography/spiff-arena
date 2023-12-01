import time

import sqlalchemy
from spiffworkflow_backend.models.db import db
from sqlalchemy.sql import text


def try_to_connect(start_time: float) -> None:
    """Try to connect."""
    try:
        db.first_or_404(text("select 1"))  # type: ignore
    except sqlalchemy.exc.DatabaseError as exception:
        if time.time() - start_time > 15:
            raise exception
        else:
            time.sleep(1)
            print("Waiting for db to be ready in loop...")  # noqa: T201
            try_to_connect(start_time)
