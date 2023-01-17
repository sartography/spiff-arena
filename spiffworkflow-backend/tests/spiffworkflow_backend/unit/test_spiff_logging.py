"""Process Model."""
from decimal import Decimal

from flask.app import Flask
from spiffworkflow_backend.models.db import db
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec

from spiffworkflow_backend.models.spiff_logging import SpiffLoggingModel


class TestSpiffLogging(BaseTest):
    """TestSpiffLogging."""

    def test_timestamps_are_stored_correctly(
        self, app: Flask, with_db_and_bpmn_file_cleanup: None
    ) -> None:
        """Test_timestamps_are_stored_correctly."""
        process_model = load_test_spec(
            "call_activity_test",
            process_model_source_directory="call_activity_same_directory",
        )

        process_instance = self.create_process_instance_from_process_model(
            process_model
        )
        bpmn_process_identifier = "test_process_identifier"
        spiff_task_guid = "test_spiff_task_guid"
        bpmn_task_identifier = "test_bpmn_task_identifier"
        timestamp = 1663250624.664887  # actual timestamp from spiff logs
        message = "test_message"
        spiff_log = SpiffLoggingModel(
            process_instance_id=process_instance.id,
            bpmn_process_identifier=bpmn_process_identifier,
            spiff_task_guid=spiff_task_guid,
            bpmn_task_identifier=bpmn_task_identifier,
            message=message,
            timestamp=timestamp,
            spiff_step=1,
        )
        assert spiff_log.timestamp == timestamp

        db.session.add(spiff_log)
        db.session.commit()

        assert spiff_log.timestamp == Decimal(str(timestamp))
