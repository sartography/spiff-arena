from __future__ import annotations

import enum
import time
from typing import Any
from typing import cast

from flask_migrate import Migrate  # type: ignore
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine.base import Connection
from sqlalchemy.orm.mapper import Mapper

db = SQLAlchemy()
migrate = Migrate()


# NOTE: ensure all db models are added to src/spiffworkflow_backend/load_database_models.py so that:
# 1) they will be loaded in time for add_listeners. otherwise they may not auto-update created_at and updated_at times
# 2) database migration code picks them up when migrations are automatically generated


def dialect_name() -> str:
    return cast(str, db.engine.dialect.name)


class SpiffworkflowBaseDBModel(db.Model):  # type: ignore
    __abstract__ = True

    @classmethod
    def _all_subclasses(cls) -> list[type[SpiffworkflowBaseDBModel]]:
        """Get all subclasses of cls, descending.

        So, if A is a subclass of B is a subclass of cls, this
        will include A and B.
        (Does not include cls)
        """
        children = cls.__subclasses__()
        result = []
        while children:
            next = children.pop()
            subclasses = next.__subclasses__()
            result.append(next)
            # check subclasses of subclasses SpiffworkflowBaseDBModel. i guess we only go down to grandchildren, which seems cool.
            for subclass in subclasses:
                children.append(subclass)
        return result

    def validate_enum_field(self, key: str, value: Any, enum_variable: enum.EnumMeta) -> Any:
        try:
            m_type = getattr(enum_variable, value, None)
        except Exception as e:
            raise ValueError(f"{self.__class__.__name__}: invalid {key}: {value}") from e

        if m_type is None:
            raise ValueError(f"{self.__class__.__name__}: invalid {key}: {value}")

        return m_type.value

    @classmethod
    def commit_with_rollback_on_exception(cls) -> None:
        """Attempts to commit the session and rolls back if it fails.

        We may need to add other error handling here as we go. But sqlalchemy insists that we
        "frame" our commits.

        https://docs.sqlalchemy.org/en/20/errors.html#error-7s2a
        https://docs.sqlalchemy.org/en/20/faq/sessions.html#faq-session-rollback
        https://docs.sqlalchemy.org/en/20/orm/session_basics.html#session-faq-whentocreate
        """
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise


def update_created_modified_on_create_listener(mapper: Mapper, _connection: Connection, target: SpiffworkflowBaseDBModel) -> None:
    """Event listener that runs before a record is updated, and sets the create/modified field accordingly."""
    if "created_at_in_seconds" in mapper.columns.keys():
        target.created_at_in_seconds = round(time.time())
    if "updated_at_in_seconds" in mapper.columns.keys():
        target.updated_at_in_seconds = round(time.time())


def update_modified_on_update_listener(mapper: Mapper, _connection: Connection, target: SpiffworkflowBaseDBModel) -> None:
    """Event listener that runs before a record is updated, and sets the modified field accordingly."""
    if "updated_at_in_seconds" in mapper.columns.keys():
        if db.session.is_modified(target, include_collections=False):
            target.updated_at_in_seconds = round(time.time())


def add_listeners() -> None:
    """Adds the listeners to all subclasses.

    This should be called after importing all subclasses
    """
    for cls in SpiffworkflowBaseDBModel._all_subclasses():
        event.listen(cls, "before_insert", update_created_modified_on_create_listener)  # type: ignore
        event.listen(cls, "before_update", update_modified_on_update_listener)  # type: ignore
