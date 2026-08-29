import importlib.util
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

_MIGRATION_PATH = (
    Path(__file__).resolve().parents[3] / "migrations" / "versions" / "7ae9aa325816_rebind_task_guid_foreign_keys.py"
)
_MIGRATION_SPEC = importlib.util.spec_from_file_location(
    "rebind_task_guid_foreign_keys",
    _MIGRATION_PATH,
)
assert _MIGRATION_SPEC is not None and _MIGRATION_SPEC.loader is not None
_MIGRATION_MODULE = importlib.util.module_from_spec(_MIGRATION_SPEC)
_MIGRATION_SPEC.loader.exec_module(_MIGRATION_MODULE)


class _BatchAlterTable:
    def __init__(self, table_name: str, events: list[str]) -> None:
        self.table_name = table_name
        self.events = events

    def __enter__(self) -> "_BatchAlterTable":
        return self

    def __exit__(self, *args: Any) -> None:
        return None

    def drop_constraint(self, name: str, *, type_: str) -> None:
        self.events.append(f"drop_constraint:{self.table_name}:{name}:{type_}")


def test_postgresql_tables_are_locked_in_parent_first_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    execute: list[str] = []
    monkeypatch.setattr(_MIGRATION_MODULE.op, "execute", execute.append)

    _MIGRATION_MODULE._lock_task_tables_parent_first()

    assert execute == [
        "LOCK TABLE task IN ACCESS EXCLUSIVE MODE",
        "LOCK TABLE future_task IN ACCESS EXCLUSIVE MODE",
        "LOCK TABLE human_task IN ACCESS EXCLUSIVE MODE",
    ]


def test_upgrade_locks_parent_before_altering_child_constraints(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []
    monkeypatch.setattr(
        _MIGRATION_MODULE.op,
        "get_bind",
        lambda: SimpleNamespace(dialect=SimpleNamespace(name="postgresql")),
    )
    monkeypatch.setattr(
        _MIGRATION_MODULE,
        "_set_postgresql_metadata_timeouts",
        lambda: events.append("set_timeouts"),
    )
    monkeypatch.setattr(
        _MIGRATION_MODULE,
        "_lock_task_tables_parent_first",
        lambda: events.append("lock_parent_first"),
    )
    monkeypatch.setattr(
        _MIGRATION_MODULE,
        "_drop_task_foreign_keys",
        lambda: events.append("drop_foreign_keys"),
    )
    monkeypatch.setattr(
        _MIGRATION_MODULE,
        "_create_task_foreign_keys",
        lambda *, not_valid=False: events.append(f"create_foreign_keys:{not_valid}"),
    )
    monkeypatch.setattr(
        _MIGRATION_MODULE.op,
        "batch_alter_table",
        lambda table_name, schema=None: _BatchAlterTable(table_name, events),
    )

    _MIGRATION_MODULE.upgrade()

    assert events == [
        "set_timeouts",
        "lock_parent_first",
        "drop_foreign_keys",
        "drop_constraint:task:guid:unique",
        "create_foreign_keys:True",
    ]


def test_downgrade_locks_parent_before_altering_child_constraints(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []
    monkeypatch.setattr(
        _MIGRATION_MODULE.op,
        "get_bind",
        lambda: SimpleNamespace(dialect=SimpleNamespace(name="postgresql")),
    )
    monkeypatch.setattr(
        _MIGRATION_MODULE.op,
        "get_context",
        lambda: SimpleNamespace(autocommit_block=nullcontext),
    )
    monkeypatch.setattr(
        _MIGRATION_MODULE.op,
        "execute",
        lambda sql: events.append(f"execute:{sql}"),
    )
    monkeypatch.setattr(
        _MIGRATION_MODULE,
        "_set_postgresql_metadata_timeouts",
        lambda: events.append("set_timeouts"),
    )
    monkeypatch.setattr(
        _MIGRATION_MODULE,
        "_lock_task_tables_parent_first",
        lambda: events.append("lock_parent_first"),
    )
    monkeypatch.setattr(
        _MIGRATION_MODULE,
        "_drop_task_foreign_keys",
        lambda: events.append("drop_foreign_keys"),
    )
    monkeypatch.setattr(
        _MIGRATION_MODULE,
        "_create_task_foreign_keys",
        lambda *, not_valid=False: events.append(f"create_foreign_keys:{not_valid}"),
    )

    _MIGRATION_MODULE.downgrade()

    assert events == [
        "execute:CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS guid ON task (guid)",
        "set_timeouts",
        "lock_parent_first",
        "drop_foreign_keys",
        "execute:ALTER TABLE task ADD CONSTRAINT guid UNIQUE USING INDEX guid",
        "create_foreign_keys:True",
    ]
