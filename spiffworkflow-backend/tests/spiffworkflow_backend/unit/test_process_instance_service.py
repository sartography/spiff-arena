"""Test_process_instance_processor."""
from flask.app import Flask
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec

from spiffworkflow_backend.models.spiff_logging import SpiffLoggingModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.process_instance_processor import (
    ProcessInstanceProcessor,
)
from spiffworkflow_backend.services.process_instance_service import (
    ProcessInstanceService,
)


class TestProcessInstanceService(BaseTest):
    """TestProcessInstanceService."""

    def test_can_create_file_data_model_for_file_data_value(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        model = ProcessInstanceService.file_data_model_for_value(
            "uploaded_file",
            "data:some/mimetype;name=testing.txt;base64,dGVzdGluZwo=",
            111,
        )
        assert model is not None
        assert model.identifier == "uploaded_file"
        assert model.process_instance_id == 111
        assert model.list_index is None
        assert model.mimetype == "some/mimetype"
        assert model.filename == "testing.txt"
        assert model.contents == b"testing\n"
        assert model.digest == "12a61f4e173fb3a11c05d6471f74728f76231b4a5fcd9667cef3af87a3ae4dc2"

    def test_does_not_create_file_data_model_for_non_file_data_value(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        model = ProcessInstanceService.file_data_model_for_value(
            "not_a_file",
            "just a value",
            111,
        )
        assert model is None

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
