from unittest.mock import MagicMock
from unittest.mock import patch

from flask import Flask

from spiffworkflow_backend.models.process_instance_metadata import ProcessInstanceMetadataModel
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.services.metadata_backfill_service import MetadataBackfillService
from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestMetadataBackfillService(BaseTest):
    def test_detect_metadata_changes(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
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

        result = MetadataBackfillService.detect_metadata_changes(
            old_model.metadata_extraction_paths, new_model.metadata_extraction_paths
        )
        assert len(result) == 1
        assert result[0]["key"] == "new_key"
        assert result[0]["path"] == "new.path"

    def test_detect_metadata_changes_with_none_values(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        old_model = ProcessModelInfo(
            id="test_model", display_name="Test Model", description="Test description", metadata_extraction_paths=None
        )

        new_model = ProcessModelInfo(
            id="test_model",
            display_name="Test Model",
            description="Test description",
            metadata_extraction_paths=[{"key": "new_key", "path": "new.path"}],
        )

        result = MetadataBackfillService.detect_metadata_changes(
            old_model.metadata_extraction_paths, new_model.metadata_extraction_paths
        )
        assert len(result) == 1
        assert result[0]["key"] == "new_key"
        assert result[0]["path"] == "new.path"

    def test_get_process_instances(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_model = self.create_process_model_with_metadata()
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
        task_data = {"outer": {"inner": "test_value"}, "invoice_number": "INV-123"}
        metadata_paths = [
            {"key": "test_key", "path": "outer.inner"},
            {"key": "invoice", "path": "invoice_number"},
            {"key": "nonexistent", "path": "does.not.exist"},
        ]
        result = ProcessModelInfo.extract_metadata(task_data, metadata_paths)
        assert result["test_key"] == "test_value"
        assert result["invoice"] == "INV-123"
        assert result["nonexistent"] is None

    @patch("spiffworkflow_backend.models.db.db.session.add")
    @patch("spiffworkflow_backend.models.process_instance_metadata.ProcessInstanceMetadataModel.query")
    def test_add_metadata_to_instance(
        self, mock_query: MagicMock, mock_add: MagicMock, app: Flask, with_db_and_bpmn_file_cleanup: None
    ) -> None:
        mock_filter = MagicMock()
        mock_first = MagicMock()
        mock_first.return_value = None
        mock_filter.first = mock_first
        mock_query.filter_by.return_value = mock_filter
        metadata = {"key1": "value1", "key2": "value2", "key3": None}
        MetadataBackfillService.add_metadata_to_instance(123, metadata)
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
        process_model = ProcessModelInfo(
            id="test_model",
            display_name="Test Model",
            description="Test model for backfill",
            metadata_extraction_paths=[{"key": "existing_key", "path": "existing.path"}],
        )
        new_metadata_paths = [{"key": "new_key", "path": "outer.inner"}]

        mock_filter = MagicMock()
        mock_metadata = MagicMock()
        mock_metadata.value = "test_value"
        mock_filter.first = MagicMock(return_value=mock_metadata)
        mock_query.filter_by = MagicMock(return_value=mock_filter)

        with patch.object(MetadataBackfillService, "get_process_instance_count", return_value=3):
            batch1 = [MagicMock(id=1), MagicMock(id=2)]
            batch2 = [MagicMock(id=3)]
            empty_batch: list = []

            get_instances_mock = MagicMock()
            get_instances_mock.side_effect = [batch1, batch2, empty_batch]

            with (
                patch.object(MetadataBackfillService, "get_process_instances", get_instances_mock),
                patch.object(MetadataBackfillService, "get_latest_task_data", return_value={"outer": {"inner": "test_value"}}),
                patch.object(ProcessModelInfo, "extract_metadata", return_value={"new_key": "test_value"}),
                patch.object(MetadataBackfillService, "add_metadata_to_instance") as mock_add_metadata,
            ):
                result = MetadataBackfillService.backfill_metadata_for_model(process_model.id, new_metadata_paths)

                assert result["instances_processed"] == 3
                assert result["instances_updated"] == 3
                assert "execution_time" in result
                assert mock_add_metadata.call_count == 3

                assert get_instances_mock.call_count == 3
                assert get_instances_mock.call_args_list[0][0][0] == process_model.id
                assert get_instances_mock.call_args_list[0][1]["offset"] == 0
                assert get_instances_mock.call_args_list[1][0][0] == process_model.id
                assert get_instances_mock.call_args_list[1][1]["offset"] == 100  # BATCH_SIZE
                assert get_instances_mock.call_args_list[2][0][0] == process_model.id
                assert get_instances_mock.call_args_list[2][1]["offset"] == 200  # BATCH_SIZE * 2

    def test_no_metadata_paths_to_backfill(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        result = MetadataBackfillService.backfill_metadata_for_model("test_model", [])
        assert result["instances_processed"] == 0
        assert result["instances_updated"] == 0
        assert result["message"] == "No new metadata paths to process"

    def test_backfill_metadata_for_model_with_real_db(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_model = self.create_process_model_with_metadata()
        task_data = {"outer": {"inner": "test_value"}, "invoice_number": "INV-123"}
        process_instance = self.create_process_instance_from_process_model(process_model)
        new_metadata_paths = [
            {"key": "new_key", "path": "outer.inner"},
        ]

        with patch.object(MetadataBackfillService, "get_latest_task_data", return_value=task_data):
            result = MetadataBackfillService.backfill_metadata_for_model(process_model.id, new_metadata_paths)
            assert result["instances_processed"] == 1
            assert result["instances_updated"] == 1
            assert "execution_time" in result

            metadata = ProcessInstanceMetadataModel.query.filter_by(
                process_instance_id=process_instance.id, key="new_key"
            ).first()

            assert metadata is not None
            assert metadata.value == "test_value"

        new_metadata_paths = [
            {"key": "new_key", "path": "outer.inner"},
        ]
        result = MetadataBackfillService.backfill_metadata_for_model(process_model.id, new_metadata_paths)

        assert result["instances_processed"] == 1
        assert result["instances_updated"] == 1
        assert "execution_time" in result

        metadata = ProcessInstanceMetadataModel.query.filter_by(process_instance_id=process_instance.id, key="new_key").first()
        assert metadata is not None
        assert metadata.value == "test_value"
