"""Test_various_bpmn_constructs."""
from flask.app import Flask
from flask.testing import FlaskClient
from tests.spiffworkflow_backend.helpers.base_test import BaseTest

from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.process_instance_processor import (
    ProcessInstanceProcessor,
)
from spiffworkflow_backend.services.process_instance_service import (
    ProcessInstanceService,
)


class TestDotNotation(BaseTest):
    """TestVariousBpmnConstructs."""

    def test_dot_notation(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_form_data_conversion_to_dot_dict."""
        process_group_id = "dot_notation_group"
        process_model_id = "test_dot_notation"
        bpmn_file_name = "diagram.bpmn"
        bpmn_file_location = "dot_notation"
        process_model_identifier = self.create_group_and_model_with_bpmn(
            client,
            with_super_admin_user,
            process_group_id=process_group_id,
            process_model_id=process_model_id,
            bpmn_file_name=bpmn_file_name,
            bpmn_file_location=bpmn_file_location,
        )

        headers = self.logged_in_headers(with_super_admin_user)
        response = self.create_process_instance_from_process_model_id(
            client, process_model_identifier, headers
        )
        process_instance_id = response.json["id"]
        process_instance = ProcessInstanceService().get_process_instance(
            process_instance_id
        )

        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)
        active_task = process_instance.active_tasks[0]

        user_task = processor.get_ready_user_tasks()[0]
        form_data = {
            "invoice.contibutorName": "Elizabeth",
            "invoice.contributorId": 100,
            "invoice.invoiceId": 10001,
            "invoice.invoiceAmount": "1000.00",
            "invoice.dueDate": "09/30/2022",
        }
        ProcessInstanceService.complete_form_task(
            processor, user_task, form_data, with_super_admin_user, active_task
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
