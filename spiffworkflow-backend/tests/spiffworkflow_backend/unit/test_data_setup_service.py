"""Process Model."""
import os
import shutil

from flask import current_app
from flask.app import Flask
from flask.testing import FlaskClient

from spiffworkflow_backend.models.reference_cache import ReferenceCacheModel
from spiffworkflow_backend.services.data_setup_service import DataSetupService
from spiffworkflow_backend.services.file_system_service import FileSystemService

from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestDataSetupService(BaseTest):
    def test_data_setup_service_finds_models(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        self.copy_example_process_models()
        DataSetupService.save_all_process_models()
        cache = ReferenceCacheModel.query.filter(ReferenceCacheModel.type == "process").all()
        assert len(cache) == 1

    def test_data_setup_service_finds_messages(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        self.copy_example_process_models()
        DataSetupService.save_all_process_models()
        cache = ReferenceCacheModel.query.filter(ReferenceCacheModel.type == "message").all()
        assert len(cache) == 4
        message_map = {c.identifier: c for c in cache}
        assert "table_seated" in message_map
        assert "order_ready" in message_map
        assert "end_of_day_receipts" in message_map
        assert "basic_message" in message_map

        assert message_map["order_ready"].relative_location == ""
        assert message_map["order_ready"].properties == {
            "correlation_keys": ["order"],
            "correlations": [
                {"correlation_property": "table_number", "retrieval_expression": "table_number"},
                {"correlation_property": "franchise_id", "retrieval_expression": "franchise_id"},
            ],
        }
        assert message_map["basic_message"].relative_location == "1-basic-concepts"
        assert message_map["basic_message"].properties == {"correlation_keys": [], "correlations": []}

    def test_data_setup_service_finds_correlations(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        self.copy_example_process_models()
        DataSetupService.save_all_process_models()
        cache = ReferenceCacheModel.query.filter(ReferenceCacheModel.type == "correlation_key").all()
        assert len(cache) == 2
        correlation_map = {c.identifier: c for c in cache}
        assert "order" in correlation_map
        assert "franchise" in correlation_map
        assert correlation_map["order"].properties == ["table_number", "franchise_id"]
        assert correlation_map["franchise"].properties == ["franchise_id"]
