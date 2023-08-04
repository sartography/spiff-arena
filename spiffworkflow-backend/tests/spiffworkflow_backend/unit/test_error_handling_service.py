import pytest
from flask import Flask
from flask.testing import FlaskClient
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.message_instance import MessageInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.workflow_execution_service import WorkflowExecutionServiceError

from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestErrorHandlingService(BaseTest):
    """Error Handling does some crazy stuff man.

    Like it can fire off BPMN messages in case a BPMN Task is waiting for that message.
    """

    def run_process_model_and_handle_error(self, process_model: ProcessModelInfo) -> ProcessInstanceModel:
        process_instance = self.create_process_instance_from_process_model(process_model)
        pip = ProcessInstanceProcessor(process_instance)

        # the error handler will be called from dequeued within do_engine_steps now
        with pytest.raises(WorkflowExecutionServiceError):
            pip.do_engine_steps(save=True)
        return process_instance

    def test_handle_error_suspends_or_faults_process(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        """Process Model in DB marked as suspended when error occurs."""
        process_model = load_test_spec(
            "test_group/error_suspend",
            process_model_source_directory="error",
            bpmn_file_name="error.bpmn",  # Slightly misnamed, it sends and receives
        )

        # Process instance should be marked as errored by default.
        process_instance = self.run_process_model_and_handle_error(process_model)
        assert ProcessInstanceStatus.error.value == process_instance.status

        # If process model should be suspended on error, then that is what should happen.
        process_model.fault_or_suspend_on_exception = "suspend"
        ProcessModelService.save_process_model(process_model)
        process_instance = self.run_process_model_and_handle_error(process_model)
        assert ProcessInstanceStatus.suspended.value == process_instance.status

    def test_error_sends_bpmn_message(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        """Real BPMN Messages should get generated and processes should fire off and complete."""
        process_model = load_test_spec(
            "test_group/error_send_message_bpmn",
            process_model_source_directory="error",
            bpmn_file_name="error.bpmn",  # Slightly misnamed, it sends and receives
        )
        """ Process Model that will listen for errors sent."""
        load_test_spec(
            "test_group/admin_tools/error_handler",
            process_model_source_directory="error",
            bpmn_file_name="error_handler.bpmn",  # Slightly misnamed, it sends and receives
        )
        process_model.exception_notification_addresses = ["dan@ILoveToReadErrorsInMyEmails.com"]
        ProcessModelService.save_process_model(process_model)
        # kick off the process and assure it got marked as an error.
        process_instance = self.run_process_model_and_handle_error(process_model)
        assert ProcessInstanceStatus.error.value == process_instance.status

        # Both send and receive messages should be generated, matched
        # and considered complete.
        messages = db.session.query(MessageInstanceModel).all()
        assert 2 == len(messages)
        assert "completed" == messages[0].status
        assert "completed" == messages[1].status
