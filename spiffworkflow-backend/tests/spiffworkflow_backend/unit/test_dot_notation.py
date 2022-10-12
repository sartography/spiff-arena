"""Test_various_bpmn_constructs."""
from flask.app import Flask
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec

from spiffworkflow_backend.services.process_instance_processor import (
    ProcessInstanceProcessor,
)
from spiffworkflow_backend.services.process_instance_service import (
    ProcessInstanceService,
)


class TestDotNotation(BaseTest):
    """TestVariousBpmnConstructs."""

    def test_dot_notation(
        self, app: Flask, with_db_and_bpmn_file_cleanup: None
    ) -> None:
        """Test_form_data_conversion_to_dot_dict."""
        process_model = load_test_spec(
            "test_dot_notation",
            bpmn_file_name="diagram.bpmn",
            process_model_source_directory="dot_notation",
        )
        current_user = self.find_or_create_user()

        process_instance = self.create_process_instance_from_process_model(
            process_model
        )
        processor = ProcessInstanceProcessor(process_instance)

        processor.do_engine_steps(save=True)

        user_task = processor.get_ready_user_tasks()[0]
        form_data = {
            "invoice.contibutorName": "Elizabeth",
            "invoice.contributorId": 100,
            "invoice.invoiceId": 10001,
            "invoice.invoiceAmount": "1000.00",
            "invoice.dueDate": "09/30/2022",
        }
        ProcessInstanceService.complete_form_task(
            processor, user_task, form_data, current_user
        )

        expected = {
            "contibutorName": "Elizabeth",
            "contributorId": 100,
            "invoiceId": 10001,
            "invoiceAmount": "1000.00",
            "dueDate": "09/30/2022",
        }

        processor.do_engine_steps(save=True)
        assert processor.get_data()["invoice"] == expected
