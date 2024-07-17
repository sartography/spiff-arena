from flask.app import Flask
from flask.testing import FlaskClient
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService

from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestDotNotation(BaseTest):
    # this used to prove the point that dot notation got converted into deeply-nested dictionaries.
    # it doesn't do that any more, and just behaves more like you would expect (flat dictionary with dots in the keys),
    # but it didn't seem obvious that the test was worthless, and this will at least prove it doesn't go back to the old behavior,
    # which would be awkward.
    def test_dot_notation_in_message_path(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_model_id = "dot_notation_group/test_dot_notation"
        bpmn_file_name = "diagram.bpmn"
        bpmn_file_location = "dot_notation"
        process_model = load_test_spec(
            process_model_id=process_model_id,
            bpmn_file_name=bpmn_file_name,
            process_model_source_directory=bpmn_file_location,
        )

        process_instance = self.create_process_instance_from_process_model(process_model)
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)
        human_task = process_instance.human_tasks[0]

        user_task = processor.get_all_ready_or_waiting_tasks()[0]
        form_data = {
            "invoice.contibutorName": "Elizabeth",
            "invoice.contributorId": 100,
            "invoice.invoiceId": 10001,
            "invoice.invoiceAmount": "1000.00",
            "invoice.dueDate": "09/30/2022",
        }
        ProcessInstanceService.complete_form_task(processor, user_task, form_data, process_instance.process_initiator, human_task)
        assert process_instance.status == ProcessInstanceStatus.complete.value

        expected = {
            "invoice.contibutorName": "Elizabeth",
            "invoice.contributorId": 100,
            "invoice.invoiceId": 10001,
            "invoice.invoiceAmount": "1000.00",
            "invoice.dueDate": "09/30/2022",
        }
        actual_data = processor.get_data()
        assert actual_data == expected
