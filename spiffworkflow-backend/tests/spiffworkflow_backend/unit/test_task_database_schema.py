from flask import Flask
from sqlalchemy import inspect

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.task import TaskModel


def test_task_guid_uses_only_the_primary_key_contract() -> None:
    guid = TaskModel.__table__.c.guid

    assert guid.primary_key is True
    assert guid.index is None
    assert guid.unique is None
    assert not any(tuple(index.columns) == (guid,) for index in TaskModel.__table__.indexes)


def test_human_task_guid_foreign_key_has_stable_migration_name() -> None:
    task_guid = HumanTaskModel.__table__.c.task_guid
    foreign_key = next(iter(task_guid.foreign_keys))

    assert foreign_key.name == "human_task_ibfk_task_guid"


def test_migrated_database_has_only_the_task_guid_primary_key(app: Flask) -> None:
    with app.app_context():
        inspector = inspect(db.engine)
        task_indexes = {index["name"] for index in inspector.get_indexes("task")}
        task_unique_constraints = {constraint["name"] for constraint in inspector.get_unique_constraints("task")}
        task_primary_key = inspector.get_pk_constraint("task")
        future_task_foreign_keys = {foreign_key["name"]: foreign_key for foreign_key in inspector.get_foreign_keys("future_task")}
        human_task_foreign_keys = {foreign_key["name"]: foreign_key for foreign_key in inspector.get_foreign_keys("human_task")}

    assert "ix_task_guid" not in task_indexes
    assert "guid" not in task_unique_constraints
    assert task_primary_key["name"] == "guid_pk"
    assert task_primary_key["constrained_columns"] == ["guid"]
    assert future_task_foreign_keys["future_task_task_guid_fk"]["referred_columns"] == ["guid"]
    assert human_task_foreign_keys["human_task_ibfk_task_guid"]["referred_columns"] == ["guid"]
