from types import SimpleNamespace
from typing import Any

from flask import Flask

from spiffworkflow_backend.models.bpmn_process import BpmnProcessModel
from spiffworkflow_backend.models.bpmn_process_definition import BpmnProcessDefinitionModel
from spiffworkflow_backend.models.task import TaskModel  # noqa: F401
from spiffworkflow_backend.models.task_definition import TaskDefinitionModel
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.task_service import TaskService
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestTaskService(BaseTest):
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
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True, execution_strategy_name="greedy")
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
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True, execution_strategy_name="greedy")
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
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True, execution_strategy_name="greedy")
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
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True, execution_strategy_name="greedy")
        spiff_task = processor.__class__.get_task_by_bpmn_identifier("my_manual_task", processor.bpmn_process_instance)
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
