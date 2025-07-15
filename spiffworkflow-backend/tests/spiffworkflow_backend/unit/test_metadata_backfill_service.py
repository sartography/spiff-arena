from unittest.mock import MagicMock
from unittest.mock import patch

from flask import Flask

from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.services.metadata_backfill_service import MetadataBackfillService
from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestMetadataBackfillService(BaseTest):
    def test_detect_metadata_changes(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        # Setup
        old_model = ProcessModelInfo(
            id="test_model",
            display_name="Test Model",
            description="Test description",
            metadata_extraction_paths=[{"key": "existing_key", "path": "existing.path"}],
        )

        new_model = ProcessModelInfo(
            id="test_model",
            display_name="Test Model",
            description="Test description",
            metadata_extraction_paths=[{"key": "existing_key", "path": "existing.path"}, {"key": "new_key", "path": "new.path"}],
        )

        # Test
        result = MetadataBackfillService.detect_metadata_changes(old_model, new_model)

        # Assert
        assert len(result) == 1
        assert result[0]["key"] == "new_key"
        assert result[0]["path"] == "new.path"

    def test_detect_metadata_changes_with_none_values(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        # Setup
        old_model = ProcessModelInfo(
            id="test_model", display_name="Test Model", description="Test description", metadata_extraction_paths=None
        )

        new_model = ProcessModelInfo(
            id="test_model",
            display_name="Test Model",
            description="Test description",
            metadata_extraction_paths=[{"key": "new_key", "path": "new.path"}],
        )

        # Test
        result = MetadataBackfillService.detect_metadata_changes(old_model, new_model)

        # Assert
        assert len(result) == 1
        assert result[0]["key"] == "new_key"
        assert result[0]["path"] == "new.path"

    def test_get_process_instances(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        # Create test process model
        process_model = self.create_process_model_with_metadata()

        # Create process instances
        instance1 = self.create_process_instance_from_process_model(process_model)
        instance2 = self.create_process_instance_from_process_model(process_model)
        instance3 = self.create_process_instance_from_process_model(process_model)

        # Test batch size 2
        instances = MetadataBackfillService.get_process_instances(process_model.id, batch_size=2)
        assert len(instances) == 2
        assert instances[0].id == instance1.id
        assert instances[1].id == instance2.id

        # Test offset
        instances = MetadataBackfillService.get_process_instances(process_model.id, batch_size=2, offset=2)
        assert len(instances) == 1
        assert instances[0].id == instance3.id

    def test_extract_metadata_for_instance(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        # Setup test data
        task_data = {"outer": {"inner": "test_value"}, "invoice_number": "INV-123"}
        metadata_paths = [
            {"key": "test_key", "path": "outer.inner"},
            {"key": "invoice", "path": "invoice_number"},
            {"key": "nonexistent", "path": "does.not.exist"},
        ]

        # Test
        result = MetadataBackfillService.extract_metadata_for_instance("test_model", task_data, metadata_paths)

        # Assert
        assert result["test_key"] == "test_value"
        assert result["invoice"] == "INV-123"
        assert result["nonexistent"] is None

    @patch("spiffworkflow_backend.models.db.db.session.add")
    @patch("spiffworkflow_backend.models.process_instance_metadata.ProcessInstanceMetadataModel.query")
    def test_add_metadata_to_instance(
        self, mock_query: MagicMock, mock_add: MagicMock, app: Flask, with_db_and_bpmn_file_cleanup: None
    ) -> None:
        # Setup
        mock_filter = MagicMock()
        mock_first = MagicMock()
        mock_first.return_value = None
        mock_filter.first = mock_first
        mock_query.filter_by.return_value = mock_filter

        # Test
        metadata = {"key1": "value1", "key2": "value2", "key3": None}
        MetadataBackfillService.add_metadata_to_instance(123, metadata)

        # Assert - should only add non-None values
        assert mock_add.call_count == 2

    @patch("spiffworkflow_backend.models.db.db.session.commit")
    @patch("spiffworkflow_backend.models.process_instance_metadata.ProcessInstanceMetadataModel.query")
    def test_backfill_metadata_for_model(
        self,
        mock_query: MagicMock,
        mock_commit: MagicMock,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        # Create a mock process model
        process_model = ProcessModelInfo(
            id="test_model",
            display_name="Test Model",
            description="Test model for backfill",
            metadata_extraction_paths=[{"key": "existing_key", "path": "existing.path"}],
        )

        # Set up metadata paths for backfill
        new_metadata_paths = [{"key": "new_key", "path": "outer.inner"}]

        # Create mock process instances
        instance_ids = [1, 2, 3]

        # Mock the filter query for verification
        mock_filter = MagicMock()
        mock_metadata = MagicMock()
        mock_metadata.value = "test_value"
        mock_filter.first = MagicMock(return_value=mock_metadata)
        mock_query.filter_by = MagicMock(return_value=mock_filter)

        # Set up a stack of mocks
        with patch.object(MetadataBackfillService, "get_process_instance_count", return_value=3):
            # Create mock instances
            mock_instances = []
            for i in instance_ids:
                mock_instance = MagicMock()
                mock_instance.id = i
                mock_instances.append(mock_instance)

            # Mock the remaining service methods
            with (
                patch.object(MetadataBackfillService, "get_process_instances", return_value=mock_instances),
                patch.object(MetadataBackfillService, "get_latest_task_data", return_value={"outer": {"inner": "test_value"}}),
                patch.object(MetadataBackfillService, "extract_metadata_for_instance", return_value={"new_key": "test_value"}),
                patch.object(MetadataBackfillService, "add_metadata_to_instance") as mock_add_metadata,
            ):
                # Run the test
                result = MetadataBackfillService.backfill_metadata_for_model(process_model.id, new_metadata_paths)

                # Verify results
                assert result["instances_processed"] == 3
                assert result["instances_updated"] == 3
                assert "execution_time" in result
                assert mock_add_metadata.call_count == 3

    def test_no_metadata_paths_to_backfill(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        # Test calling backfill with empty metadata paths
        result = MetadataBackfillService.backfill_metadata_for_model("test_model", [])
        assert result["instances_processed"] == 0
        assert result["instances_updated"] == 0
        assert result["message"] == "No new metadata paths to process"
