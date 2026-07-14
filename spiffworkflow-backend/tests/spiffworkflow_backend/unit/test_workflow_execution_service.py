from datetime import datetime
from types import SimpleNamespace
from typing import Any
from typing import cast

import pytest
from flask import Flask
from SpiffWorkflow.util.task import TaskState  # type: ignore

from spiffworkflow_backend.models.future_task import FutureTaskModel
from spiffworkflow_backend.models.task import TaskModel  # noqa: F401
from spiffworkflow_backend.services.process_instance_runtime import ProcessInstanceRuntime
from spiffworkflow_backend.services.workflow_execution_service import WorkflowExecutionService
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestWorkflowExecutionService(BaseTest):
    @staticmethod
    def execution_service_with_timer_value(timer_value: Any) -> WorkflowExecutionService:
        event = SimpleNamespace(event_type="DurationTimerEventDefinition", value=timer_value)
        event_definition = SimpleNamespace(details=lambda _spiff_task: event)
        spiff_task = SimpleNamespace(
            id="timer-task-guid",
            state=TaskState.WAITING,
            task_spec=SimpleNamespace(event_definition=event_definition),
            internal_data={},
        )
        execution_service = WorkflowExecutionService.__new__(WorkflowExecutionService)
        execution_service.bpmn_process_instance = cast(Any, SimpleNamespace(get_tasks=lambda state: [spiff_task]))
        execution_service.process_instance_model = cast(Any, SimpleNamespace())
        return execution_service

    def test_schedule_waiting_timer_events_ignores_uninitialized_value(
        self,
        app: Flask,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        insert_calls = []
        execution_service = self.execution_service_with_timer_value(None)
        monkeypatch.setattr(
            execution_service,
            "is_happening_soon",
            lambda _run_at: pytest.fail("An uninitialized timer should not be considered for queueing"),
        )
        monkeypatch.setattr(FutureTaskModel, "insert_or_update", lambda **kwargs: insert_calls.append(kwargs))

        with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_CELERY_ENABLED", True):
            execution_service.schedule_waiting_timer_events()

        assert insert_calls == []

    def test_schedule_waiting_timer_events_persists_initialized_value(
        self,
        app: Flask,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        timer_value = "2026-07-11T03:00:00+00:00"
        insert_calls = []
        execution_service = self.execution_service_with_timer_value(timer_value)
        monkeypatch.setattr(execution_service, "is_happening_soon", lambda _run_at: False)
        monkeypatch.setattr(FutureTaskModel, "insert_or_update", lambda **kwargs: insert_calls.append(kwargs))

        with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_CELERY_ENABLED", True):
            execution_service.schedule_waiting_timer_events()

        assert insert_calls == [
            {
                "guid": "timer-task-guid",
                "run_at_in_seconds": round(datetime.fromisoformat(timer_value).timestamp()),
                "queued_to_run_at_in_seconds": None,
            }
        ]

    def test_schedule_waiting_timer_events_rejects_malformed_initialized_value(
        self,
        app: Flask,
    ) -> None:
        execution_service = self.execution_service_with_timer_value("not-an-iso-timestamp")

        with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_CELERY_ENABLED", True):
            with pytest.raises(ValueError):
                execution_service.schedule_waiting_timer_events()

    def test_saves_last_milestone_appropriately(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_model = load_test_spec(
            "test_group/test-last-milestone",
            process_model_source_directory="test-last-milestone",
        )
        process_instance = self.create_process_instance_from_process_model(process_model)
        runtime = ProcessInstanceRuntime(process_instance)
        runtime.do_engine_steps(save=True, execution_strategy_name="greedy")
        assert process_instance.last_milestone_bpmn_name == "Started"

        self.complete_next_manual_task(runtime)
        assert process_instance.last_milestone_bpmn_name == "In Call Activity"
        self.complete_next_manual_task(runtime)
        assert process_instance.last_milestone_bpmn_name == "Done with call activity"
        self.complete_next_manual_task(runtime)
        assert process_instance.last_milestone_bpmn_name == "Completed"
        assert process_instance.status == "complete"

    def test_boundary_event_priority(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_model = load_test_spec(
            "test_group/prioritize-boundary-event",
            process_model_source_directory="prioritize-boundary-event",
        )
        process_instance = self.create_process_instance_from_process_model(process_model)
        runtime = ProcessInstanceRuntime(process_instance)
        runtime.do_engine_steps(save=True, execution_strategy_name="greedy")
        assert process_instance.status == "complete"
        assert runtime.bpmn_process_instance.data == {"testOk": True}
