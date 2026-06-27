from __future__ import annotations

from typing import Any

from flask.app import Flask

from spiffworkflow_backend.services.workflow_execution_service import EngineStepDelegate
from spiffworkflow_backend.services.workflow_execution_service import QueueInstructionsForEndUserExecutionStrategy
from spiffworkflow_backend.services.workflow_execution_service import TaskRunnability


class FakeDelegate(EngineStepDelegate):
    def will_complete_task(self, spiff_task: Any) -> None:
        pass

    def did_complete_task(self, spiff_task: Any) -> None:
        pass

    def add_object_to_db_session(self, bpmn_process_instance: Any) -> None:
        pass

    def after_engine_steps(self, bpmn_process_instance: Any) -> None:
        pass

    def on_exception(self, bpmn_process_instance: Any) -> None:
        pass

    def last_completed_spiff_task(self) -> None:
        return None


def test_queue_instruction_strategy_breaks_after_max_tasks(app: Flask) -> None:
    app.config["SPIFFWORKFLOW_BACKEND_AUTO_SAVE_MAX_TASKS"] = 3
    app.config["SPIFFWORKFLOW_BACKEND_AUTO_SAVE_MAX_SECONDS"] = 999
    strategy = QueueInstructionsForEndUserExecutionStrategy(FakeDelegate())

    assert strategy.should_break_after([object(), object()]) is False
    assert strategy.should_break_after([object()]) is True
    assert strategy.task_runnability_when_breaking_after() == TaskRunnability.has_ready_tasks


def test_queue_instruction_strategy_breaks_after_max_seconds(app: Flask, monkeypatch: Any) -> None:
    times = iter([100.0, 103.0])
    monkeypatch.setattr("spiffworkflow_backend.services.workflow_execution_service.time.monotonic", lambda: next(times))
    app.config["SPIFFWORKFLOW_BACKEND_AUTO_SAVE_MAX_TASKS"] = 999
    app.config["SPIFFWORKFLOW_BACKEND_AUTO_SAVE_MAX_SECONDS"] = 3
    strategy = QueueInstructionsForEndUserExecutionStrategy(FakeDelegate())

    assert strategy.should_break_after([object()]) is True
