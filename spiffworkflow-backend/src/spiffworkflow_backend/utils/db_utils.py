"""Database utility functions for common operations."""

from collections.abc import Mapping
from collections.abc import Sequence
from typing import Any

from flask import current_app
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import OperationalError

from spiffworkflow_backend.models.db import db

MYSQL_DUPLICATE_ENTRY_ERROR_CODE = 1062
MYSQL_DEADLOCK_ERROR_CODE = 1213


def dbapi_error_code(exception: Exception) -> int | None:
    original_exception = getattr(exception, "orig", None)
    original_args = getattr(original_exception, "args", ())
    if not original_args:
        return None

    try:
        return int(original_args[0])
    except (TypeError, ValueError):
        return None


def is_mysql_deadlock_error(exception: Exception) -> bool:
    return (
        current_app.config["SPIFFWORKFLOW_BACKEND_DATABASE_TYPE"] == "mysql"
        and isinstance(exception, OperationalError)
        and dbapi_error_code(exception) == MYSQL_DEADLOCK_ERROR_CODE
    )


def insert_or_ignore_duplicate(
    model_class: type,
    values: Mapping[str, Any] | Sequence[Mapping[str, Any]],
    postgres_conflict_index_elements: list[str] | None = None,
) -> Any:
    """Insert records, ignoring duplicates to avoid MySQL deadlocks.

    This function provides a database-agnostic way to insert records while
    handling duplicate key conflicts differently for MySQL, PostgreSQL, and SQLite:

    - MySQL: Uses naive insert with IntegrityError catching (errno 1062) to
      avoid deadlocks from ON DUPLICATE KEY UPDATE. Processes records one-by-one
      when given a list to avoid batch upsert deadlock issues.
    - PostgreSQL/SQLite: Uses on_conflict_do_nothing which doesn't have deadlock issues.

    Args:
        model_class: The SQLAlchemy model class to insert into
        values: Single dict-like object or sequence of dict-like objects to insert
        postgres_conflict_index_elements: Index column names for PostgreSQL's
            on_conflict clause (e.g., ["hash"] or ["id", "name"]). If omitted,
            PostgreSQL ignores conflicts on any unique constraint.

    Returns:
        For single record MySQL insert: Result object or None if duplicate exists
        For batch MySQL insert: None (no return value)
        For PostgreSQL/SQLite: Result from db.session.execute()
    """
    is_mysql = current_app.config["SPIFFWORKFLOW_BACKEND_DATABASE_TYPE"] == "mysql"
    is_batch = isinstance(values, Sequence) and not isinstance(values, str | bytes)

    if is_mysql:
        # For MySQL, use naive insert to avoid deadlocks from ON DUPLICATE KEY UPDATE.
        if is_batch:
            # We iterate one-by-one since MySQL lacks a deadlock-free batch upsert equivalent.
            for value_dict in values:
                try:
                    db.session.execute(mysql_insert(model_class).values(value_dict))
                except IntegrityError as e:
                    # Check if it's a duplicate key error (errno 1062)
                    if dbapi_error_code(e) == MYSQL_DUPLICATE_ENTRY_ERROR_CODE:
                        # Record already exists, this is expected and fine
                        continue
                    # Some other integrity error, re-raise
                    raise
            return None
        else:
            # Single record insert
            try:
                result = db.session.execute(mysql_insert(model_class).values(values))
                return result
            except IntegrityError as e:
                # Check if it's a duplicate key error (errno 1062)
                if dbapi_error_code(e) == MYSQL_DUPLICATE_ENTRY_ERROR_CODE:
                    # Record already exists, return None to signal no insert occurred
                    return None
                # Some other integrity error, re-raise
                raise
    else:
        # PostgreSQL and SQLite on_conflict_do_nothing don't have deadlock issues.
        if current_app.config["SPIFFWORKFLOW_BACKEND_DATABASE_TYPE"] == "sqlite":
            insert_stmt = sqlite_insert(model_class).values(values)
        else:
            insert_stmt = postgres_insert(model_class).values(values)
        if postgres_conflict_index_elements is None:
            on_duplicate_key_stmt = insert_stmt.on_conflict_do_nothing()
        else:
            on_duplicate_key_stmt = insert_stmt.on_conflict_do_nothing(index_elements=postgres_conflict_index_elements)
        return db.session.execute(on_duplicate_key_stmt)
