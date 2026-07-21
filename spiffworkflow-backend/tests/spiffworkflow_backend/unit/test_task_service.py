from types import SimpleNamespace
from typing import Any

import pytest
from flask import Flask
from sqlalchemy.orm import make_transient_to_detached

from spiffworkflow_backend.models.bpmn_process import BpmnProcessModel
from spiffworkflow_backend.models.bpmn_process_definition import BpmnProcessDefinitionModel
from spiffworkflow_backend.models.task import TaskModel  # noqa: F401
from spiffworkflow_backend.models.task_definition import TaskDefinitionModel
from spiffworkflow_backend.services.process_instance_runtime import ProcessInstanceRuntime
from spiffworkflow_backend.services.task_service import TaskModelError
from spiffworkflow_backend.services.task_service import TaskService
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestTaskService(BaseTest):
    def test_task_model_error_includes_error_message(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(TaskModelError, "get_task_trace", classmethod(lambda cls, task_model: []))

        error = TaskModelError("the task failed", task_model=object())  # type: ignore[arg-type]

        assert "the task failed" in str(error)

    def test_can_get_full_bpmn_process_path(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        bpmn_file_names = [
            "call_activity_level_3",
            "call_activity_level_2b",
            "call_activity_level_2",
        ]
        for bpmn_file_name in bpmn_file_names:
            load_test_spec(
                f"test_group/{bpmn_file_name}",
                process_model_source_directory="call_activity_nested",
                bpmn_file_name=bpmn_file_name,
            )
        process_model = load_test_spec(
            "test_group/call_activity_nested",
            process_model_source_directory="call_activity_nested",
            bpmn_file_name="call_activity_nested",
        )
        process_instance = self.create_process_instance_from_process_model(process_model)
        runtime = ProcessInstanceRuntime(process_instance)
        runtime.do_engine_steps(save=True, execution_strategy_name="greedy")
        assert process_instance.status == "complete"

        bpmn_process_level_2b = (
            BpmnProcessModel.query.join(BpmnProcessDefinitionModel)
            .filter(BpmnProcessDefinitionModel.bpmn_identifier == "Level2b")
            .order_by(BpmnProcessModel.id)
            .first()
        )
        assert bpmn_process_level_2b is not None
        full_bpnmn_process_path = TaskService.full_bpmn_process_path(bpmn_process_level_2b)
        assert full_bpnmn_process_path == ["Level1", "Level2", "Level2b"]

        bpmn_process_level_3 = (
            BpmnProcessModel.query.join(BpmnProcessDefinitionModel)
            .filter(BpmnProcessDefinitionModel.bpmn_identifier == "Level3")
            .order_by(BpmnProcessModel.id)
            .first()
        )
        assert bpmn_process_level_3 is not None
        full_bpnmn_process_path = TaskService.full_bpmn_process_path(bpmn_process_level_3)
        assert full_bpnmn_process_path == ["Level1", "Level2", "Level3"]

    def test_task_models_of_parent_bpmn_processes_stop_on_first_call_activity(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        bpmn_file_names = [
            "call_activity_level_3",
            "call_activity_level_2b",
            "call_activity_level_2",
        ]
        for bpmn_file_name in bpmn_file_names:
            load_test_spec(
                f"test_group/{bpmn_file_name}",
                process_model_source_directory="call_activity_nested",
                bpmn_file_name=bpmn_file_name,
            )
        process_model = load_test_spec(
            "test_group/call_activity_nested",
            process_model_source_directory="call_activity_nested",
            bpmn_file_name="call_activity_nested",
        )
        process_instance = self.create_process_instance_from_process_model(process_model)
        runtime = ProcessInstanceRuntime(process_instance)
        runtime.do_engine_steps(save=True, execution_strategy_name="greedy")
        assert process_instance.status == "complete"

        task_model_level_2b = (
            TaskModel.query.join(TaskDefinitionModel)
            .filter(TaskDefinitionModel.bpmn_identifier == "level_2b_subprocess_script_task")
            .first()
        )
        assert task_model_level_2b is not None
        (bpmn_processes, task_models) = TaskService.task_models_of_parent_bpmn_processes(
            task_model_level_2b, stop_on_first_call_activity=True
        )
        assert len(bpmn_processes) == 2
        assert len(task_models) == 2
        assert bpmn_processes[0].bpmn_process_definition.bpmn_identifier == "Level2b"
        # either of these is valid since we are not pinning the task model query to one or the other
        # and they are both call activities and not the top level process
        assert task_models[0].task_definition.bpmn_identifier in ["level2b_second_call", "Level1_CallLevel_2B"]

        task_model_level_3 = (
            TaskModel.query.join(TaskDefinitionModel).filter(TaskDefinitionModel.bpmn_identifier == "level_3_script_task").first()
        )
        assert task_model_level_3 is not None
        (bpmn_processes, task_models) = TaskService.task_models_of_parent_bpmn_processes(
            task_model_level_3, stop_on_first_call_activity=True
        )
        assert len(bpmn_processes) == 1
        assert len(task_models) == 1
        assert bpmn_processes[0].bpmn_process_definition.bpmn_identifier == "Level3"
        assert task_models[0].task_definition.bpmn_identifier == "level3"

    def test_bpmn_process_for_called_activity_or_top_level_process(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        bpmn_file_names = [
            "call_activity_level_3",
            "call_activity_level_2b",
            "call_activity_level_2",
        ]
        for bpmn_file_name in bpmn_file_names:
            load_test_spec(
                f"test_group/{bpmn_file_name}",
                process_model_source_directory="call_activity_nested",
                bpmn_file_name=bpmn_file_name,
            )
        process_model = load_test_spec(
            "test_group/call_activity_nested",
            process_model_source_directory="call_activity_nested",
            bpmn_file_name="call_activity_nested",
        )
        process_instance = self.create_process_instance_from_process_model(process_model)
        runtime = ProcessInstanceRuntime(process_instance)
        runtime.do_engine_steps(save=True, execution_strategy_name="greedy")
        assert process_instance.status == "complete"

        task_model_level_2b = (
            TaskModel.query.join(TaskDefinitionModel)
            .filter(TaskDefinitionModel.bpmn_identifier == "level_2b_subprocess_script_task")
            .first()
        )
        assert task_model_level_2b is not None
        bpmn_process = TaskService.bpmn_process_for_called_activity_or_top_level_process(task_model_level_2b)
        assert bpmn_process is not None
        assert bpmn_process.bpmn_process_definition.bpmn_identifier == "Level2b"

        task_model_level_3 = (
            TaskModel.query.join(TaskDefinitionModel).filter(TaskDefinitionModel.bpmn_identifier == "level_3_script_task").first()
        )
        assert task_model_level_3 is not None
        bpmn_process = TaskService.bpmn_process_for_called_activity_or_top_level_process(task_model_level_3)
        assert bpmn_process.bpmn_process_definition.bpmn_identifier == "Level3"

    def test_get_button_labels_for_waiting_signal_event_tasks(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_model = load_test_spec(
            "test_group/signal_event_extensions",
            process_model_source_directory="signal_event_extensions",
            bpmn_file_name="signal_event_extensions",
        )
        process_instance = self.create_process_instance_from_process_model(process_model)
        runtime = ProcessInstanceRuntime(process_instance)
        runtime.do_engine_steps(save=True, execution_strategy_name="greedy")
        spiff_task = runtime.__class__.get_task_by_bpmn_identifier("my_manual_task", runtime.bpmn_process_instance)
        assert spiff_task is not None

        events = TaskService.get_ready_signals_with_button_labels(process_instance.id, str(spiff_task.id))
        assert len(events) == 1
        signal_event = events[0]
        assert signal_event["event"]["name"] == "eat_spam"
        assert signal_event["event"]["typename"] == "SignalEventDefinition"
        assert signal_event["label"] == "Eat Spam"

    def test_sync_parents_for_deleted_spiff_tasks_updates_ancestors_once_and_skips_deleted_ancestors(
        self,
        app: Flask,
    ) -> None:
        task_service: Any = TaskService.__new__(TaskService)
        updated_guids: list[str] = []

        def capture_update(spiff_task: SimpleNamespace, store_process_instance_events: bool = True) -> None:
            updated_guids.append(spiff_task.id)

        task_service.update_task_model_with_spiff_task = capture_update

        grandparent = SimpleNamespace(id="grandparent", parent=None)
        deleted_parent = SimpleNamespace(id="deleted_parent", parent=grandparent)
        deleted_a = SimpleNamespace(id="deleted_a", parent=deleted_parent)
        deleted_b = SimpleNamespace(id="deleted_b", parent=deleted_parent)

        TaskService.sync_parents_for_deleted_spiff_tasks(
            task_service,
            [deleted_a, deleted_b],
            {"deleted_a", "deleted_b", "deleted_parent"},
        )

        assert updated_guids == ["grandparent"]

    def test_prune_missing_child_references_removes_dangling_guids(
        self,
        app: Flask,
    ) -> None:
        task_service: Any = TaskService.__new__(TaskService)
        task_service.task_models = {
            "parent": SimpleNamespace(
                properties_json={"children": ["child_a", "missing_child", "child_b"]},
            ),
            "untouched": SimpleNamespace(
                properties_json={"children": ["child_c"]},
            ),
        }

        TaskService.prune_missing_child_references(task_service, {"parent", "child_a", "child_b", "child_c"})

        assert task_service.task_models["parent"].properties_json["children"] == ["child_a", "child_b"]
        assert task_service.task_models["untouched"].properties_json["children"] == ["child_c"]

    def test_find_or_create_task_model_uses_mapping_before_querying(
        self,
        app: Flask,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        task_model = TaskModel(guid="task-1")
        make_transient_to_detached(task_model)
        task_service: Any = TaskService.__new__(TaskService)
        task_service.task_model_mapping = {"task-1": task_model}
        task_service._should_query_task_models = True

        def fail_filter_by(**_kwargs: Any) -> None:
            pytest.fail("TaskModel.query.filter_by should not be called for a task_model_mapping hit")

        monkeypatch.setattr(TaskModel, "query", SimpleNamespace(filter_by=fail_filter_by))

        bpmn_process, found_task_model = task_service.find_or_create_task_model_from_spiff_task(SimpleNamespace(id="task-1"))

        assert bpmn_process is None
        assert found_task_model is task_model

    def test_find_or_create_task_model_queries_for_transient_mapping_entry(
        self,
        app: Flask,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        transient_task_model = TaskModel(guid="task-1")
        persisted_task_model = TaskModel(guid="task-1")
        make_transient_to_detached(persisted_task_model)
        filter_by_calls = []
        task_service: Any = TaskService.__new__(TaskService)
        task_service.task_model_mapping = {"task-1": transient_task_model}
        task_service._should_query_task_models = True

        class TaskModelQuery:
            def filter_by(self, **kwargs: Any) -> "TaskModelQuery":
                filter_by_calls.append(kwargs)
                return self

            def first(self) -> TaskModel:
                return persisted_task_model

        monkeypatch.setattr(TaskModel, "query", TaskModelQuery())

        bpmn_process, found_task_model = task_service.find_or_create_task_model_from_spiff_task(SimpleNamespace(id="task-1"))

        assert filter_by_calls == [{"guid": "task-1"}]
        assert bpmn_process is None
        assert found_task_model is persisted_task_model

    def test_find_or_create_task_model_queries_when_mapping_misses(
        self,
        app: Flask,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        task_model = SimpleNamespace(guid="task-1")
        filter_by_calls = []
        task_service: Any = TaskService.__new__(TaskService)
        task_service.task_model_mapping = {"other-task": SimpleNamespace(guid="other-task")}
        task_service._should_query_task_models = True

        class TaskModelQuery:
            def filter_by(self, **kwargs: Any) -> "TaskModelQuery":
                filter_by_calls.append(kwargs)
                return self

            def first(self) -> Any:
                return task_model

        monkeypatch.setattr(TaskModel, "query", TaskModelQuery())

        bpmn_process, found_task_model = task_service.find_or_create_task_model_from_spiff_task(SimpleNamespace(id="task-1"))

        assert filter_by_calls == [{"guid": "task-1"}]
        assert bpmn_process is None
        assert found_task_model is task_model

    def test_add_tasks_to_bpmn_process_uses_mapping_before_querying(
        self,
        app: Flask,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        task_id = "00000000-0000-0000-0000-000000000001"
        task_model = TaskModel(guid=task_id)
        make_transient_to_detached(task_model)
        spiff_task = SimpleNamespace(
            id=task_id,
            has_state=lambda _state: False,
        )
        task_service: Any = TaskService.__new__(TaskService)
        task_service.task_model_mapping = {task_id: task_model}
        task_service._should_query_task_models = True
        task_service.task_models = {}

        def fail_filter_by(**_kwargs: Any) -> None:
            pytest.fail("TaskModel.query.filter_by should not be called for a task_model_mapping hit")

        def fail_create_task(*_args: Any, **_kwargs: Any) -> None:
            pytest.fail("TaskService._create_task should not be called for a task_model_mapping hit")

        monkeypatch.setattr(TaskModel, "query", SimpleNamespace(filter_by=fail_filter_by))
        monkeypatch.setattr(TaskService, "_create_task", fail_create_task)
        task_service.update_task_model = lambda _task_model, _spiff_task: None

        task_service.add_tasks_to_bpmn_process(
            tasks={task_id: {}},
            spiff_workflow=SimpleNamespace(get_task_from_id=lambda _task_uuid: spiff_task),
            bpmn_process=SimpleNamespace(),
        )

        assert task_service.task_models == {task_id: task_model}
