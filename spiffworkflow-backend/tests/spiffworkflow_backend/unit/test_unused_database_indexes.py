from flask import Flask
from sqlalchemy import inspect

from spiffworkflow_backend.models.bpmn_process import BpmnProcessModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_instance_event import ProcessInstanceEventModel
from spiffworkflow_backend.models.task import TaskModel

REMOVED_INDEXES_BY_TABLE = {
    "bpmn_process": {"ix_bpmn_process_json_data_hash"},
    "process_instance_event": {
        "ix_process_instance_event_event_type",
        "ix_process_instance_event_timestamp",
    },
    "task": {
        "ix_task_json_data_hash",
        "ix_task_python_env_data_hash",
        "ix_task_state",
    },
}


def test_models_do_not_declare_unused_runtime_indexes() -> None:
    models = (BpmnProcessModel, ProcessInstanceEventModel, TaskModel)
    declared_indexes = {index.name for model in models for index in model.__table__.indexes}

    for removed_indexes in REMOVED_INDEXES_BY_TABLE.values():
        assert declared_indexes.isdisjoint(removed_indexes)


def test_migrated_database_does_not_have_unused_runtime_indexes(
    app: Flask,
) -> None:
    with app.app_context():
        inspector = inspect(db.engine)
        indexes_by_table = {
            table: {index["name"] for index in inspector.get_indexes(table)} for table in REMOVED_INDEXES_BY_TABLE
        }

    for table, removed_indexes in REMOVED_INDEXES_BY_TABLE.items():
        assert indexes_by_table[table].isdisjoint(removed_indexes)


def test_process_event_user_foreign_key_index_is_retained() -> None:
    user_id = ProcessInstanceEventModel.__table__.c.user_id

    assert user_id.index is True
