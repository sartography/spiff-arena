from flask import Flask
from spiffworkflow_backend.models.task import TaskModel  # noqa: F401
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor

from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestWorkflowExecutionService(BaseTest):
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
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True, execution_strategy_name="greedy")
        assert process_instance.last_milestone_bpmn_name == "Started"

        self.complete_next_manual_task(processor)
        assert process_instance.last_milestone_bpmn_name == "In Call Activity"
        self.complete_next_manual_task(processor)
        assert process_instance.last_milestone_bpmn_name == "Done with call activity"
        self.complete_next_manual_task(processor)
        assert process_instance.last_milestone_bpmn_name == "Completed"
        assert process_instance.status == "complete"
