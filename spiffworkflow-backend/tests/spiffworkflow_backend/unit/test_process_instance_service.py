"""Test_process_instance_processor."""
from flask.app import Flask
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec

from spiffworkflow_backend.models.spiff_logging import SpiffLoggingModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.process_instance_processor import (
    ProcessInstanceProcessor,
)


class TestProcessInstanceService(BaseTest):
    """TestProcessInstanceService."""

    def test_does_not_log_set_data_when_calling_engine_steps_on_waiting_call_activity(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_does_not_log_set_data_when_calling_engine_steps_on_waiting_call_activity."""
        process_model = load_test_spec(
            process_model_id="test_group/call-activity-to-human-task",
            process_model_source_directory="call-activity-to-human-task",
        )
        process_instance = self.create_process_instance_from_process_model(
            process_model=process_model, user=with_super_admin_user
        )
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)

        process_instance_logs = SpiffLoggingModel.query.filter_by(
            process_instance_id=process_instance.id
        ).all()
        initial_length = len(process_instance_logs)

        # ensure we have something in the logs
        assert initial_length > 0

        # logs should NOT increase after running this a second time since it's just waiting on a human task
        processor.do_engine_steps(save=True)
        process_instance_logs = SpiffLoggingModel.query.filter_by(
            process_instance_id=process_instance.id
        ).all()
        assert len(process_instance_logs) == initial_length
