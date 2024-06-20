from typing import Any

from flask import current_app

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.message_model import MessageCorrelationPropertyModel
from spiffworkflow_backend.models.message_model import MessageModel
from spiffworkflow_backend.models.process_group import ProcessGroup


class MessageDefinitionService:
    @classmethod
    def _message_model_from_message(
        cls, identifier: str, message_definition: dict[str, Any], process_group: ProcessGroup
    ) -> MessageModel | None:
        schema = message_definition.get("schema", "{}")

        return MessageModel(identifier=identifier, location=process_group.id, schema=schema)

    @classmethod
    def _correlation_property_models_from_message_definition(
        cls, correlation_property_group: dict[str, Any], location: str
    ) -> list[MessageCorrelationPropertyModel]:
        models: list[MessageCorrelationPropertyModel] = []

        for identifier, definition in correlation_property_group.items():
            retrieval_expression = definition.get("retrieval_expression")

            if not retrieval_expression:
                current_app.logger.debug(f"Malformed correlation property: '{identifier}' in file @ '{location}'")
                continue

            models.append(MessageCorrelationPropertyModel(identifier=identifier, retrieval_expression=retrieval_expression))

        return models

    @classmethod
    def collect_message_models(
        cls, process_group: ProcessGroup, location: str, all_message_models: dict[tuple[str, str], MessageModel]
    ) -> None:
        messages: dict[str, Any] = process_group.messages or {}

        for message_identifier, message_definition in messages.items():
            message_model = cls._message_model_from_message(message_identifier, message_definition, process_group)
            if message_model is None:
                continue
            all_message_models[(message_model.identifier, message_model.location)] = message_model

            correlation_property_models = cls._correlation_property_models_from_message_definition(
                message_definition.get("correlation_properties", {}), location
            )

            message_model.correlation_properties = correlation_property_models  # type: ignore

    @classmethod
    def delete_all_message_models(cls) -> None:
        messages = MessageModel.query.all()
        for message in messages:
            db.session.delete(message)

    @classmethod
    def delete_message_models_at_location(cls, location: str) -> None:
        messages = MessageModel.query.filter_by(location=location).all()
        for message in messages:
            db.session.delete(message)

    @classmethod
    def save_all_message_models(cls, all_message_models: dict[tuple[str, str], MessageModel]) -> None:
        for message_model in all_message_models.values():
            db.session.add(message_model)

            for correlation_property_model in message_model.correlation_properties:
                db.session.add(correlation_property_model)
