from types import SimpleNamespace
from typing import Any

import pytest

from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts import delete_process_instances_with_criteria as script_module
from spiffworkflow_backend.scripts.delete_process_instances_with_criteria import DeleteProcessInstancesWithCriteria


class FakeColumn:
    __hash__ = object.__hash__

    def __eq__(self, other: object) -> "FakeColumn":  # type: ignore[override]
        return self

    def __and__(self, other: object) -> "FakeColumn":
        return self

    def __lt__(self, other: object) -> "FakeColumn":
        return self

    def __invert__(self) -> "FakeColumn":
        return self

    def in_(self, other: object) -> "FakeColumn":
        return self

    def notlike(self, other: object) -> "FakeColumn":
        return self


class FakeQuery:
    def __init__(self, results: list[SimpleNamespace]):
        self.results = results
        self.limit_value: int | None = None

    def filter(self, *args: Any) -> "FakeQuery":
        return self

    def order_by(self, *args: Any) -> "FakeQuery":
        return self

    def limit(self, limit: int) -> "FakeQuery":
        self.limit_value = limit
        return self

    def all(self) -> list[SimpleNamespace]:
        return self.results[: self.limit_value]


class FakeSession:
    def __init__(self) -> None:
        self.deleted: list[SimpleNamespace] = []
        self.committed = False
        self.added: list[Any] = []

    def delete(self, model: SimpleNamespace) -> None:
        self.deleted.append(model)

    def add(self, model: Any) -> None:
        self.added.append(model)

    def commit(self) -> None:
        self.committed = True


def test_delete_process_instances_with_criteria_returns_summary_and_honors_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    results = [
        SimpleNamespace(id=1, process_model_identifier="cleanup/model-a", status="complete"),
        SimpleNamespace(id=2, process_model_identifier="cleanup/model-a", status="complete"),
        SimpleNamespace(id=3, process_model_identifier="cleanup/model-a", status="error"),
        SimpleNamespace(id=4, process_model_identifier="cleanup/model-b", status="complete"),
        SimpleNamespace(id=5, process_model_identifier="cleanup/model-b", status="complete"),
    ]
    session = FakeSession()
    fake_process_instance_model = SimpleNamespace(
        id=FakeColumn(),
        process_model_identifier=FakeColumn(),
        status=FakeColumn(),
        updated_at_in_seconds=FakeColumn(),
        query=FakeQuery(results),
    )
    monkeypatch.setattr(script_module, "ProcessInstanceModel", fake_process_instance_model)
    monkeypatch.setattr(script_module, "db", SimpleNamespace(session=session))
    monkeypatch.setattr(script_module, "or_", lambda *args: args)

    criteria = [
        {"status": ["complete", "error"], "last_updated_delta": 60, "exclude_name_prefixes": ["cleanup/reaper"]},
        {"name": "cleanup/model-b", "status": ["complete"], "last_updated_delta": 60},
    ]
    script_attributes_context = ScriptAttributesContext(
        task=None,
        environment_identifier="unit_testing",
        process_instance_id=1,
        process_model_identifier="cleanup/reaper",
    )

    summary = DeleteProcessInstancesWithCriteria().run(script_attributes_context, criteria, limit=4, return_summary=True)

    assert summary == {
        "total_deleted": 4,
        "limit": 4,
        "criteria_count": 2,
        "by_model_status": [
            {"process_model_identifier": "cleanup/model-a", "status": "complete", "deleted": 2},
            {"process_model_identifier": "cleanup/model-a", "status": "error", "deleted": 1},
            {"process_model_identifier": "cleanup/model-b", "status": "complete", "deleted": 1},
        ],
    }
    assert session.deleted == results[:4]
    assert session.committed is True


def test_delete_process_instances_with_criteria_keeps_integer_return_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    results = [
        SimpleNamespace(id=1, process_model_identifier="cleanup/model-a", status="complete"),
        SimpleNamespace(id=2, process_model_identifier="cleanup/model-a", status="complete"),
    ]
    fake_process_instance_model = SimpleNamespace(
        id=FakeColumn(),
        process_model_identifier=FakeColumn(),
        status=FakeColumn(),
        updated_at_in_seconds=FakeColumn(),
        query=FakeQuery(results),
    )
    monkeypatch.setattr(script_module, "ProcessInstanceModel", fake_process_instance_model)
    monkeypatch.setattr(script_module, "db", SimpleNamespace(session=FakeSession()))
    monkeypatch.setattr(script_module, "or_", lambda *args: args)

    rows_affected = DeleteProcessInstancesWithCriteria().run(
        ScriptAttributesContext(
            task=None,
            environment_identifier="unit_testing",
            process_instance_id=1,
            process_model_identifier="cleanup/reaper",
        ),
        [{"name": "cleanup/model-a", "status": ["complete"], "last_updated_delta": 60}],
        limit=1,
    )

    assert rows_affected == 1
