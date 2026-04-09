from flask.app import Flask
from starlette.testclient import TestClient

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.message_model import MessageModel
from spiffworkflow_backend.models.reference_cache import Reference
from spiffworkflow_backend.models.reference_cache import ReferenceCacheModel
from spiffworkflow_backend.services.data_setup_service import DataSetupService
from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestDataSetupService(BaseTest):
    def test_data_setup_service_finds_models(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        self.copy_example_process_models()
        DataSetupService.refresh_process_model_caches()
        cache = ReferenceCacheModel.query.filter(ReferenceCacheModel.type == "process").all()
        assert len(cache) == 1

    def test_data_setup_service_finds_messages(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        self.copy_example_process_models()
        DataSetupService.refresh_process_model_caches()
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

    def test_build_message_usage_map_tracks_nearest_message_model_location(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        references = [
            Reference(
                identifier="Process_1",
                display_name="Residential",
                relative_location="order/residential/residential",
                type="process",
                file_name="residential.bpmn",
                messages={"request-for-information-received": {}},
                correlations={},
                start_messages=[],
                called_element_ids=[],
                properties={},
            ),
            Reference(
                identifier="Process_2",
                display_name="Request For Information",
                relative_location="order/request-for-information/request-for-information",
                type="process",
                file_name="request-for-information.bpmn",
                messages={"request-for-information-received": {}},
                correlations={},
                start_messages=[],
                called_element_ids=[],
                properties={},
            ),
        ]

        all_message_models = {
            ("request-for-information-received", "order"): None,
            ("request-for-information-received", "order/request-for-information"): None,
        }

        usage_map = DataSetupService._build_message_usage_map(references, all_message_models)

        assert usage_map == {
            ("request-for-information-received", "order"): ["order/residential/residential"],
            ("request-for-information-received", "order/request-for-information"): [
                "order/request-for-information/request-for-information"
            ],
        }

    def test_update_message_usage_for_process_model_tracks_nearest_message_model_location(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        parent_message = MessageModel(
            identifier="request-for-information-received",
            location="order",
            schema={},
            process_model_identifiers=[],
        )
        child_message = MessageModel(
            identifier="request-for-information-received",
            location="order/request-for-information",
            schema={},
            process_model_identifiers=[],
        )
        db.session.add(parent_message)
        db.session.add(child_message)
        db.session.commit()

        process_model_id = "order/request-for-information/request-for-information"
        references = [
            Reference(
                identifier="Process_2",
                display_name="Request For Information",
                relative_location=process_model_id,
                type="process",
                file_name="request-for-information.bpmn",
                messages={"request-for-information-received": {}},
                correlations={},
                start_messages=[],
                called_element_ids=[],
                properties={},
            ),
        ]

        DataSetupService._update_message_usage_for_process_model(process_model_id, references)

        db.session.refresh(parent_message)
        db.session.refresh(child_message)

        assert parent_message.process_model_identifiers == []
        assert child_message.process_model_identifiers == [process_model_id]
