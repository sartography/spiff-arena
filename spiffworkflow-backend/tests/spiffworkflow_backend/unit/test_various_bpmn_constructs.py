from SpiffWorkflow.util.task import TaskState
from flask.app import Flask
from flask.testing import FlaskClient

from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestVariousBpmnConstructs(BaseTest):
    def test_running_process_with_timer_intermediate_catch_event(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_model = load_test_spec(
            process_model_id="test_group/timer_intermediate_catch_event",
            process_model_source_directory="timer_intermediate_catch_event",
        )
        process_instance = self.create_process_instance_from_process_model(process_model)
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)

    def test_can_update_conditional_intermediate_catch_event(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_model = load_test_spec(
            process_model_id="test_group/conditional_catch_event",
            process_model_source_directory="conditional_catch_event",
        )
        process_instance = self.create_process_instance_from_process_model(process_model)
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)
        ready_or_waiting_tasks = processor.get_all_ready_or_waiting_tasks()
        assert len(ready_or_waiting_tasks) == 2
        task_a = next((t for t in ready_or_waiting_tasks if t.task_spec.bpmn_id == "task_a"), None)
        assert task_a is not None
        assert task_a.state == TaskState.READY
        event_one = next((t for t in ready_or_waiting_tasks if t.task_spec.bpmn_id == "event_1"), None)
        assert event_one is not None
        assert event_one.state == TaskState.WAITING

        processor.bpmn_process_instance.refresh_waiting_tasks()
        processor.bpmn_process_instance.refresh_waiting_tasks()
        processor.do_engine_steps(save=True)
        self.complete_next_manual_task(processor)
        processor.bpmn_process_instance.refresh_waiting_tasks()
        processor.bpmn_process_instance.refresh_waiting_tasks()
        processor.bpmn_process_instance.refresh_waiting_tasks()
        processor.do_engine_steps(save=True)
        processor.bpmn_process_instance.refresh_waiting_tasks()
        processor.do_engine_steps(save=True)
        ready_or_waiting_tasks = processor.get_all_ready_or_waiting_tasks()
        assert len(ready_or_waiting_tasks) == 0
