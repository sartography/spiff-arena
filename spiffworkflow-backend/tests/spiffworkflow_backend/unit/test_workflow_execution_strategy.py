from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from typing import cast

from flask.app import Flask
from SpiffWorkflow.specs.base import TaskSpec  # type: ignore
from SpiffWorkflow.specs.WorkflowSpec import WorkflowSpec  # type: ignore
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore

from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.services.bpmn_process_service import BpmnProcessService
from spiffworkflow_backend.services.workflow_execution_service import EngineStepDelegate
from spiffworkflow_backend.services.workflow_execution_service import QueueInstructionsForEndUserExecutionStrategy
from spiffworkflow_backend.services.workflow_execution_service import TaskModelSavingDelegate
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


class FakeWorkflow:
    def refresh_due_waiting_tasks(self) -> None:
        pass

    def get_tasks(self, **kwargs: Any) -> list[Any]:
        return []

    def is_completed(self) -> bool:
        return False


class TaskWorkflow:
    def __init__(self) -> None:
        self.tasks: dict[str, SpiffTask] = {}


def spiff_task(name: str) -> SpiffTask:
    return SpiffTask(TaskWorkflow(), TaskSpec(WorkflowSpec("test"), name))


def task_model_saving_strategy() -> QueueInstructionsForEndUserExecutionStrategy:
    process_instance = ProcessInstanceModel(
        id=1,
        process_model_identifier="test/process",
        process_model_display_name="test/process",
        process_initiator_id=1,
        status="running",
    )
    return QueueInstructionsForEndUserExecutionStrategy(
        TaskModelSavingDelegate(BpmnProcessService.serializer, process_instance, {})
    )


def test_queue_instruction_strategy_breaks_after_max_tasks(app: Flask) -> None:
    app.config["SPIFFWORKFLOW_BACKEND_AUTO_SAVE_MAX_TASKS"] = 3
    app.config["SPIFFWORKFLOW_BACKEND_AUTO_SAVE_MAX_SECONDS"] = 999
    strategy = QueueInstructionsForEndUserExecutionStrategy(FakeDelegate())

    assert strategy.should_break_after([object(), object()]) is False
    assert strategy.should_break_after([object()]) is True


def test_queue_instruction_strategy_breaks_after_max_seconds(app: Flask, monkeypatch: Any) -> None:
    times = iter([100.0, 103.0])
    monkeypatch.setattr("spiffworkflow_backend.services.workflow_execution_service.time.monotonic", lambda: next(times))
    app.config["SPIFFWORKFLOW_BACKEND_AUTO_SAVE_MAX_TASKS"] = 999
    app.config["SPIFFWORKFLOW_BACKEND_AUTO_SAVE_MAX_SECONDS"] = 3
    strategy = QueueInstructionsForEndUserExecutionStrategy(FakeDelegate())

    assert strategy.should_break_after([object()]) is True


def test_queue_instruction_strategy_reports_no_ready_tasks_after_autosave(app: Flask, monkeypatch: Any) -> None:
    app.config["SPIFFWORKFLOW_BACKEND_AUTO_SAVE_MAX_TASKS"] = 1
    app.config["SPIFFWORKFLOW_BACKEND_AUTO_SAVE_MAX_SECONDS"] = 999
    strategy = QueueInstructionsForEndUserExecutionStrategy(FakeDelegate())
    engine_step_batches = iter([[SimpleNamespace(task_spec=SimpleNamespace(extensions={}))], []])
    monkeypatch.setattr(strategy, "get_ready_engine_steps", lambda bpmn_process_instance: next(engine_step_batches))
    monkeypatch.setattr(strategy, "_run_and_did_complete", lambda spiff_task: None)

    task_runnability = strategy.spiff_run(FakeWorkflow(), cast(ProcessInstanceModel, SimpleNamespace(id=1)))

    assert task_runnability == TaskRunnability.no_ready_tasks


def test_queue_instruction_strategy_caps_ready_batch_at_max_tasks(app: Flask) -> None:
    app.config["SPIFFWORKFLOW_BACKEND_AUTO_SAVE_MAX_TASKS"] = 3
    app.config["SPIFFWORKFLOW_BACKEND_AUTO_SAVE_MAX_SECONDS"] = 999
    strategy = task_model_saving_strategy()
    ready_tasks = [spiff_task(str(i)) for i in range(5)]

    assert strategy.engine_steps_to_run(ready_tasks) == ready_tasks[:3]
