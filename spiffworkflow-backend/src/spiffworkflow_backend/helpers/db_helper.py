"""Db_helper."""
import time

import sqlalchemy
from sqlalchemy.sql import text

from spiffworkflow_backend.models.db import db


def try_to_connect(start_time: float) -> None:
    """Try to connect."""
    try:
        db.first_or_404(text("select 1"))  # type: ignore
    except sqlalchemy.exc.DatabaseError as exception:
        if time.time() - start_time > 15:
            raise exception
        else:
            time.sleep(1)
            print("Waiting for db to be ready in loop...")
            try_to_connect(start_time)
