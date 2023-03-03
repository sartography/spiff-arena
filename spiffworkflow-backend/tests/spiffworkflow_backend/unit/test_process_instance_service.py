"""Test_process_instance_processor."""
from typing import Optional

from flask.app import Flask
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec

from spiffworkflow_backend.models.process_instance_file_data import (
    ProcessInstanceFileDataModel,
)
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

    SAMPLE_FILE_DATA = "data:some/mimetype;name=testing.txt;base64,dGVzdGluZwo="
    SAMPLE_DIGEST_REFERENCE = "data:some/mimetype;name=testing.txt;base64,12a61f4e173fb3a11c05d6471f74728f76231b4a5fcd9667cef3af87a3ae4dc2"  # noqa: B950

    def _check_sample_file_data_model(
        self,
        identifier: str,
        list_index: Optional[int],
        model: Optional[ProcessInstanceFileDataModel],
    ) -> None:
        assert model is not None
        assert model.identifier == identifier
        assert model.process_instance_id == 111
        assert model.list_index == list_index
        assert model.mimetype == "some/mimetype"
        assert model.filename == "testing.txt"
        assert model.contents == b"testing\n"  # type: ignore
        assert (
            model.digest
            == "12a61f4e173fb3a11c05d6471f74728f76231b4a5fcd9667cef3af87a3ae4dc2"
        )

    def test_can_create_file_data_model_for_file_data_value(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        model = ProcessInstanceService.file_data_model_for_value(
            "uploaded_file",
            self.SAMPLE_FILE_DATA,
            111,
        )
        self._check_sample_file_data_model("uploaded_file", None, model)

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

    def test_can_create_file_data_models_for_single_file_data_values(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        data = {
            "uploaded_file": self.SAMPLE_FILE_DATA,
        }
        models = ProcessInstanceService.file_data_models_for_data(data, 111)

        assert len(models) == 1
        self._check_sample_file_data_model("uploaded_file", None, models[0])

    def test_can_create_file_data_models_for_multiple_file_data_values(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        data = {
            "uploaded_files": [self.SAMPLE_FILE_DATA, self.SAMPLE_FILE_DATA],
        }
        models = ProcessInstanceService.file_data_models_for_data(data, 111)

        assert len(models) == 2
        self._check_sample_file_data_model("uploaded_files", 0, models[0])
        self._check_sample_file_data_model("uploaded_files", 1, models[1])

    def test_can_create_file_data_models_for_fix_of_file_data_and_non_file_data_values(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        data = {
            "not_a_file": "just a value",
            "uploaded_file": self.SAMPLE_FILE_DATA,
            "not_a_file2": "just a value 2",
            "uploaded_files": [self.SAMPLE_FILE_DATA, self.SAMPLE_FILE_DATA],
            "not_a_file3": "just a value 3",
            "uploaded_files2": [self.SAMPLE_FILE_DATA, self.SAMPLE_FILE_DATA],
            "uploaded_file2": self.SAMPLE_FILE_DATA,
        }
        models = ProcessInstanceService.file_data_models_for_data(data, 111)

        assert len(models) == 6
        self._check_sample_file_data_model("uploaded_file", None, models[0])
        self._check_sample_file_data_model("uploaded_files", 0, models[1])
        self._check_sample_file_data_model("uploaded_files", 1, models[2])
        self._check_sample_file_data_model("uploaded_files2", 0, models[3])
        self._check_sample_file_data_model("uploaded_files2", 1, models[4])
        self._check_sample_file_data_model("uploaded_file2", None, models[5])

    def test_does_not_create_file_data_models_for_non_file_data_values(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        data = {
            "not_a_file": "just a value",
        }
        models = ProcessInstanceService.file_data_models_for_data(data, 111)

        assert len(models) == 0

    def test_can_replace_file_data_values_with_digest_references(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        data = {
            "uploaded_file": self.SAMPLE_FILE_DATA,
            "uploaded_files": [self.SAMPLE_FILE_DATA, self.SAMPLE_FILE_DATA],
        }
        models = ProcessInstanceService.file_data_models_for_data(data, 111)
        ProcessInstanceService.replace_file_data_with_digest_references(data, models)

        assert data == {
            "uploaded_file": self.SAMPLE_DIGEST_REFERENCE,
            "uploaded_files": [
                self.SAMPLE_DIGEST_REFERENCE,
                self.SAMPLE_DIGEST_REFERENCE,
            ],
        }

    def test_does_not_replace_non_file_data_values_with_digest_references(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        data = {
            "not_a_file": "just a value",
        }
        models = ProcessInstanceService.file_data_models_for_data(data, 111)
        ProcessInstanceService.replace_file_data_with_digest_references(data, models)

        assert len(data) == 1
        assert data["not_a_file"] == "just a value"

    def test_can_replace_file_data_values_with_digest_references_when_non_file_data_values_are_present(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        data = {
            "not_a_file": "just a value",
            "uploaded_file": self.SAMPLE_FILE_DATA,
            "not_a_file2": "just a value2",
            "uploaded_files": [self.SAMPLE_FILE_DATA, self.SAMPLE_FILE_DATA],
            "not_a_file3": "just a value3",
        }
        models = ProcessInstanceService.file_data_models_for_data(data, 111)
        ProcessInstanceService.replace_file_data_with_digest_references(data, models)

        assert data == {
            "not_a_file": "just a value",
            "uploaded_file": self.SAMPLE_DIGEST_REFERENCE,
            "not_a_file2": "just a value2",
            "uploaded_files": [
                self.SAMPLE_DIGEST_REFERENCE,
                self.SAMPLE_DIGEST_REFERENCE,
            ],
            "not_a_file3": "just a value3",
        }

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
