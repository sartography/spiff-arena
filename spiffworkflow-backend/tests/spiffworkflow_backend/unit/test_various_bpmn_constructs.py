"""Test_various_bpmn_constructs."""
from flask.app import Flask
from flask.testing import FlaskClient
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestVariousBpmnConstructs(BaseTest):
    """TestVariousBpmnConstructs."""

    def test_running_process_with_timer_intermediate_catch_event(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel
    ) -> None:
        """Test_running_process_with_timer_intermediate_catch_event."""
        process_model_identifier = self.basic_test_setup(
            client,
            with_super_admin_user,
            "test_group",
            "timer_intermediate_catch_event"
        )

        process_model = ProcessModelService().get_process_model(
            process_model_id=process_model_identifier
        )

        process_instance = self.create_process_instance_from_process_model(
            process_model
        )
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)
