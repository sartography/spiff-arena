from flask.app import Flask
from flask.testing import FlaskClient
from spiffworkflow_backend.models.message_model import MessageModel
from spiffworkflow_backend.models.reference_cache import ReferenceCacheModel
from spiffworkflow_backend.services.data_setup_service import DataSetupService

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
        message_models = MessageModel.query.all()
        assert len(message_models) == 4
        message_map = {model.identifier: model for model in message_models}

        assert "table_seated" in message_map
        assert "order_ready" in message_map
        assert "end_of_day_receipts" in message_map
        assert "basic_message" in message_map

        assert message_map["order_ready"].location == "examples"

        correlations = {cp.identifier: cp.retrieval_expression for cp in message_map["order_ready"].correlation_properties}
        assert correlations == {"table_number": "table_number", "franchise_id": "franchise_id"}

        assert message_map["basic_message"].location == "examples/1-basic-concepts"
        assert message_map["basic_message"].correlation_properties == []
