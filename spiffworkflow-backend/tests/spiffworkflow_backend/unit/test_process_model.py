"""Process Model."""
from flask.app import Flask
from flask_bpmn.models.db import db
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec

from spiffworkflow_backend.models.bpmn_process_id_lookup import BpmnProcessIdLookup
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.services.process_instance_processor import (
    ProcessInstanceProcessor,
)


class TestProcessModel(BaseTest):
    """TestProcessModel."""

    def test_initializes_files_as_empty_array(self) -> None:
        """Test_initializes_files_as_empty_array."""
        process_model_one = self.create_test_process_model(
            id="model_one", display_name="Model One"
        )
        assert process_model_one.files == []

    def test_can_run_process_model_with_call_activities_when_in_same_process_model_directory(
        self, app: Flask, with_db_and_bpmn_file_cleanup: None
    ) -> None:
        """Test_can_run_process_model_with_call_activities."""
        process_model = load_test_spec(
            "call_activity_test",
            process_model_source_directory="call_activity_same_directory",
        )

        process_instance = self.create_process_instance_from_process_model(
            process_model
        )
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)
        assert process_instance.status == "complete"

    def test_can_run_process_model_with_call_activities_when_not_in_same_directory(
        self, app: Flask, with_db_and_bpmn_file_cleanup: None
    ) -> None:
        """Test_can_run_process_model_with_call_activities."""
        process_model = load_test_spec(
            "call_activity_nested",
            process_model_source_directory="call_activity_nested",
            bpmn_file_name="call_activity_nested",
        )

        bpmn_file_names = [
            "call_activity_level_2b",
            "call_activity_level_2",
            "call_activity_level_3",
        ]
        for bpmn_file_name in bpmn_file_names:
            load_test_spec(
                bpmn_file_name,
                process_model_source_directory="call_activity_nested",
                bpmn_file_name=bpmn_file_name,
            )
        process_instance = self.create_process_instance_from_process_model(
            process_model
        )
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)
        assert process_instance.status == "complete"

    def test_can_run_process_model_with_call_activities_when_process_identifier_is_not_in_database(
        self, app: Flask, with_db_and_bpmn_file_cleanup: None
    ) -> None:
        """Test_can_run_process_model_with_call_activities."""
        process_model = load_test_spec(
            "call_activity_nested",
            process_model_source_directory="call_activity_nested",
            bpmn_file_name="call_activity_nested",
        )

        bpmn_file_names = [
            "call_activity_level_2b",
            "call_activity_level_2",
            "call_activity_level_3",
        ]
        for bpmn_file_name in bpmn_file_names:
            load_test_spec(
                bpmn_file_name,
                process_model_source_directory="call_activity_nested",
                bpmn_file_name=bpmn_file_name,
            )
        process_instance = self.create_process_instance_from_process_model(
            process_model
        )

        # delete all of the id lookup items to force to processor to find the correct
        # process model when running the process
        db.session.query(BpmnProcessIdLookup).delete()
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)
        assert process_instance.status == "complete"

    def create_test_process_model(self, id: str, display_name: str) -> ProcessModelInfo:
        """Create_test_process_model."""
        return ProcessModelInfo(
            id=id,
            display_name=display_name,
            description=display_name,
        )
