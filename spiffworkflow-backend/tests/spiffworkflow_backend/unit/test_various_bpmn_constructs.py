"""Test_various_bpmn_constructs."""
from flask.app import Flask
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec

from spiffworkflow_backend.services.process_instance_processor import (
    ProcessInstanceProcessor,
)


class TestVariousBpmnConstructs(BaseTest):
    """TestVariousBpmnConstructs."""

    def test_running_process_with_timer_intermediate_catch_event(
        self, app: Flask, with_db_and_bpmn_file_cleanup: None
    ) -> None:
        """Test_running_process_with_timer_intermediate_catch_event."""
        process_model = load_test_spec(
            "timers_intermediate_catch_event",
            process_model_source_directory="timer_intermediate_catch_event",
        )

        process_instance = self.create_process_instance_from_process_model(
            process_model
        )
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)
