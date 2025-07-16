from unittest.mock import MagicMock
from unittest.mock import patch

from flask import Flask

from spiffworkflow_backend.background_processing.celery_tasks.metadata_backfill_task import _celery_task_backfill_metadata_impl
from spiffworkflow_backend.background_processing.celery_tasks.metadata_backfill_task import trigger_metadata_backfill
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestMetadataBackfillTask(BaseTest):
    @patch("spiffworkflow_backend.background_processing.celery_tasks.metadata_backfill_task.MetadataBackfillService")
    def test_celery_task_backfill_metadata(
        self,
        mock_metadata_backfill_service: MagicMock,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        mock_backfill_result = {
            "instances_processed": 10,
            "instances_updated": 5,
            "execution_time": 1.23,
            "message": "Successfully processed 10 instances, updated 5",
        }
        mock_metadata_backfill_service.backfill_metadata_for_model.return_value = mock_backfill_result
        mock_self = MagicMock()
        mock_self.request.id = "test-task-id"

        metadata_paths = [{"key": "test_key", "path": "test.path"}]
        result = _celery_task_backfill_metadata_impl("test-task-id", "test_process_model", metadata_paths)

        mock_metadata_backfill_service.backfill_metadata_for_model.assert_called_once_with("test_process_model", metadata_paths)

        assert result["ok"] is True
        assert result["process_model_identifier"] == "test_process_model"
        assert result["statistics"] == mock_backfill_result

    @patch("spiffworkflow_backend.background_processing.celery_tasks.metadata_backfill_task.MetadataBackfillService")
    def test_celery_task_backfill_metadata_with_exception(
        self,
        mock_metadata_backfill_service: MagicMock,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        mock_metadata_backfill_service.backfill_metadata_for_model.side_effect = ValueError("Test error")
        mock_self = MagicMock()
        mock_self.request.id = "test-task-id"

        metadata_paths = [{"key": "test_key", "path": "test.path"}]
        result = _celery_task_backfill_metadata_impl("test-task-id", "test_process_model", metadata_paths)

        assert result["ok"] is False
        assert result["process_model_identifier"] == "test_process_model"
        assert result["error"] == "Test error"

    @patch("spiffworkflow_backend.background_processing.celery_tasks.metadata_backfill_task.current_app")
    @patch("spiffworkflow_backend.background_processing.celery_tasks.metadata_backfill_task.MetadataBackfillService")
    @patch("spiffworkflow_backend.background_processing.celery_tasks.metadata_backfill_task.celery_task_backfill_metadata")
    def test_trigger_metadata_backfill(
        self,
        mock_task: MagicMock,
        mock_service: MagicMock,
        mock_current_app: MagicMock,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        mock_current_app.config = {"SPIFFWORKFLOW_BACKEND_PROCESS_INSTANCE_METADATA_BACKFILL_ENABLED": True}

        # Create mock models with different metadata paths
        old_model = ProcessModelInfo(
            id="test_model",
            display_name="Test Model",
            description="Test Description",
            metadata_extraction_paths=[{"key": "existing", "path": "existing.path"}],
        )
        new_model = ProcessModelInfo(
            id="test_model",
            display_name="Test Model",
            description="Test Description",
            metadata_extraction_paths=[{"key": "existing", "path": "existing.path"}, {"key": "new_key", "path": "new.path"}],
        )

        mock_service.detect_metadata_changes.return_value = [{"key": "new_key", "path": "new.path"}]
        mock_task_result = MagicMock()
        mock_task_result.id = "test-task-id"
        mock_task.delay.return_value = mock_task_result

        result = trigger_metadata_backfill(old_model.id, old_model.metadata_extraction_paths, new_model.metadata_extraction_paths)

        mock_service.detect_metadata_changes.assert_called_once_with(
            old_model.metadata_extraction_paths, new_model.metadata_extraction_paths
        )
        mock_task.delay.assert_called_once_with("test_model", [{"key": "new_key", "path": "new.path"}])

        assert result["status"] == "triggered"
        assert result["task_id"] == "test-task-id"
        assert result["process_model_id"] == "test_model"
        assert result["new_metadata_paths"] == ["new_key"]

    @patch("spiffworkflow_backend.background_processing.celery_tasks.metadata_backfill_task.current_app")
    def test_trigger_metadata_backfill_disabled(
        self,
        mock_current_app: MagicMock,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        mock_current_app.config = {"SPIFFWORKFLOW_BACKEND_PROCESS_INSTANCE_METADATA_BACKFILL_ENABLED": False}
        old_model = ProcessModelInfo(id="test_model", display_name="Test Model", description="Test")
        new_model = ProcessModelInfo(id="test_model", display_name="Test Model", description="Test")
        result = trigger_metadata_backfill(old_model.id, old_model.metadata_extraction_paths, new_model.metadata_extraction_paths)

        assert result["status"] == "skipped"
        assert result["reason"] == "Metadata backfill feature is disabled"

    @patch("spiffworkflow_backend.background_processing.celery_tasks.metadata_backfill_task.current_app")
    @patch("spiffworkflow_backend.background_processing.celery_tasks.metadata_backfill_task.MetadataBackfillService")
    def test_trigger_metadata_backfill_no_new_paths(
        self,
        mock_service: MagicMock,
        mock_current_app: MagicMock,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        mock_current_app.config = {"SPIFFWORKFLOW_BACKEND_PROCESS_INSTANCE_METADATA_BACKFILL_ENABLED": True}
        mock_service.detect_metadata_changes.return_value = []

        old_model = ProcessModelInfo(id="test_model", display_name="Test Model", description="Test")
        new_model = ProcessModelInfo(id="test_model", display_name="Test Model", description="Test")
        result = trigger_metadata_backfill(old_model.id, old_model.metadata_extraction_paths, new_model.metadata_extraction_paths)

        assert result["status"] == "skipped"
        assert result["reason"] == "No new metadata paths detected"
