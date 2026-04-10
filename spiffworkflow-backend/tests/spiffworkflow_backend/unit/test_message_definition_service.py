from flask.app import Flask

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.message_model import MessageModel
from spiffworkflow_backend.models.process_group import ProcessGroup
from spiffworkflow_backend.services.message_definition_service import MessageDefinitionService
from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestMessageDefinitionService(BaseTest):
    def test_preserves_process_model_identifiers_when_usage_map_is_not_provided(
        self, app: Flask, with_db_and_bpmn_file_cleanup: None
    ) -> None:
        existing_message_model = MessageModel(
            identifier="request-for-information-received",
            location="order",
            schema={},
            process_model_identifiers=["order/request-for-information"],
        )
        db.session.add(existing_message_model)
        db.session.commit()

        process_group = ProcessGroup(id="order", display_name="Order")
        message_model = MessageDefinitionService._message_model_from_message(
            "request-for-information-received",
            {"schema": {}},
            process_group,
        )

        assert message_model is not None
        assert message_model.process_model_identifiers == ["order/request-for-information"]

        MessageDefinitionService.delete_message_models_at_location("order")
        db.session.commit()

        MessageDefinitionService.save_all_message_models(
            {
                (
                    "request-for-information-received",
                    "order",
                ): message_model
            }
        )
        db.session.commit()

        refreshed_message_model = MessageModel.query.filter_by(
            identifier="request-for-information-received",
            location="order",
        ).one()
        assert refreshed_message_model.process_model_identifiers == ["order/request-for-information"]
