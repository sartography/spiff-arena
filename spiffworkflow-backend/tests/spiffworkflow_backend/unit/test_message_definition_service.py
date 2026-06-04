import pytest
from flask.app import Flask
from sqlalchemy.exc import IntegrityError

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.message_model import MessageModel
from spiffworkflow_backend.models.process_group import ProcessGroup
from spiffworkflow_backend.services.message_definition_service import MessageDefinitionConflictError
from spiffworkflow_backend.services.message_definition_service import MessageDefinitionService
from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestMessageDefinitionService(BaseTest):
    def test_descendant_location_detects_more_specific_target(self) -> None:
        assert MessageDefinitionService._is_descendant_location(
            "order",
            "order/request-for-information",
        )
        assert not MessageDefinitionService._is_descendant_location(
            "order/request-for-information",
            "order",
        )
        assert not MessageDefinitionService._is_descendant_location(
            "order",
            "order-archive",
        )

    def test_out_of_scope_process_model_identifiers_returns_usages_that_cannot_see_target_location(self) -> None:
        out_of_scope_process_model_identifiers = MessageDefinitionService._out_of_scope_process_model_identifiers(
            [
                "order/order-process",
                "order/request-for-information/request-for-information",
            ],
            "order/request-for-information",
        )

        assert out_of_scope_process_model_identifiers == ["order/order-process"]

    def test_format_process_model_identifiers_for_move_error_truncates_after_two_models(self) -> None:
        assert (
            MessageDefinitionService._format_process_model_identifiers_for_move_error(
                [
                    "order/first-process",
                    "order/second-process",
                    "order/third-process",
                    "order/fourth-process",
                ]
            )
            == "order/first-process, order/second-process, and 2 more"
        )

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

    def test_save_rejects_supplied_message_id_for_different_location(
        self, app: Flask, with_db_and_bpmn_file_cleanup: None
    ) -> None:
        existing_message_model = MessageModel(
            identifier="request-for-information-received",
            location="order",
            schema={},
        )
        db.session.add(existing_message_model)
        db.session.commit()

        message_model = MessageModel(
            identifier="request-for-information-received",
            location="order/request-for-information",
            schema={},
        )
        message_model.id = existing_message_model.id

        with pytest.raises(ValueError, match="belongs to a different message"):
            MessageDefinitionService.save_all_message_models(
                {
                    (
                        "request-for-information-received",
                        "order/request-for-information",
                    ): message_model
                }
            )

    def test_save_raises_conflict_when_supplied_message_id_is_inserted_concurrently(
        self, app: Flask, with_db_and_bpmn_file_cleanup: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        message_model = MessageModel(
            identifier="request-for-information-received",
            location="order",
            schema={},
        )
        message_model.id = 123

        def raise_integrity_error() -> None:
            raise IntegrityError("insert", {}, Exception("duplicate key"))

        monkeypatch.setattr(db.session, "flush", raise_integrity_error)

        try:
            with pytest.raises(MessageDefinitionConflictError, match="created concurrently"):
                MessageDefinitionService.save_all_message_models(
                    {
                        (
                            "request-for-information-received",
                            "order",
                        ): message_model
                    }
                )
        finally:
            db.session.rollback()
