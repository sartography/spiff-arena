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

    def test_can_separate_uploaded_file_from_submitted_data(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        data = {
            "good_key": "hey there",
            "bad_key": "data:...",
        }
        file_uploads, other_data = ProcessInstanceService.separate_file_uploads_from_submitted_data(data)
        assert len(file_uploads) == 1
        assert "bad_key" in file_uploads
        assert len(other_data) == 1
        assert "good_key" in other_data

    def test_can_separate_uploaded_files_from_submitted_data(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        data = {
            "good_key": "hey there",
            "bad_key": ["data:...", "data:..."],
        }
        file_uploads, other_data = ProcessInstanceService.separate_file_uploads_from_submitted_data(data)
        assert len(file_uploads) == 1
        assert "bad_key" in file_uploads
        assert len(other_data) == 1
        assert "good_key" in other_data

    def test_separate_file_uploads_does_not_mind_key_types(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        data = {
            "str_key": "hey there",
            "int_key": 33,
            "dict_key": {"a": 1},
            "list_key": [1, 2, 3],
        }
        file_uploads, other_data = ProcessInstanceService.separate_file_uploads_from_submitted_data(data)
        assert len(file_uploads) == 0
        assert other_data == data

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
