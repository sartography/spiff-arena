"""Db_helper."""
import sqlalchemy
from flask_bpmn.models.db import db
import time


def try_to_connect(start_time: float) -> None:
    """Try to connect."""
    try:
        db.first_or_404("select 1")  # type: ignore
    except sqlalchemy.exc.DatabaseError as exception:
        if time.time() - start_time > 15:
            raise exception
        else:
            time.sleep(1)
            try_to_connect(start_time)
