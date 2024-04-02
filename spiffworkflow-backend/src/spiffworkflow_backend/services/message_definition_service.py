from typing import Any

from flask import current_app

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.message_model import MessageCorrelationPropertyModel
from spiffworkflow_backend.models.message_model import MessageModel
from spiffworkflow_backend.models.process_group import ProcessGroup


class MessageDefinitionService:
    @classmethod
    def _message_model_from_message(
        cls, message: dict[str, Any], process_group: ProcessGroup, location: str
    ) -> MessageModel | None:
        identifier = message.get("id")
        schema = message.get("schema", "{}")

        if identifier is None:
            current_app.logger.debug(f"Malformed message: '{message}' in @ '{location}'")
            return None

        return MessageModel(identifier=identifier, location=location, schema=schema)

    @classmethod
    def _correlation_property_models_from_group(
        cls, correlation_property_group: list[dict[str, Any]], location: str
    ) -> dict[str, list[MessageCorrelationPropertyModel]]:
        models: dict[str, list[MessageCorrelationPropertyModel]] = {}

        for item in correlation_property_group:
            identifier = item.get("id")
            retrieval_expressions = item.get("retrieval_expressions")

            if not identifier or not retrieval_expressions:
                current_app.logger.debug(f"Malformed correlation property: '{item}' in file @ '{location}'")
                continue

            for expression in retrieval_expressions:
                message_identifier = expression.get("message_ref")
                retrieval_expression = expression.get("formal_expression")

                if not message_identifier or not retrieval_expression:
                    current_app.logger.debug(f"Malformed retrieval expression: '{expression}' in file @ '{location}'")
                    continue

                if message_identifier not in models:
                    models[message_identifier] = []

                models[message_identifier].append(
                    MessageCorrelationPropertyModel(identifier=identifier, retrieval_expression=retrieval_expression)
                )

        return models

    @classmethod
    def collect_message_models(
        cls, process_group: ProcessGroup, location: str, all_message_models: dict[tuple[str, str], MessageModel]
    ) -> None:
        messages = process_group.messages or []
        local_message_models = {}

        for message in messages:
            message_model = cls._message_model_from_message(message, process_group, location)
            if message_model is None:
                continue
            local_message_models[message_model.identifier] = message_model
            all_message_models[(message_model.identifier, message_model.location)] = message_model

        correlation_property_models_by_message_identifier = cls._correlation_property_models_from_group(
            process_group.correlation_properties or [], location
        )

        for message_identifier, correlation_property_models in correlation_property_models_by_message_identifier.items():
            message_model = local_message_models.get(message_identifier)

            if message_model is None:
                current_app.logger.debug(
                    f"Correlation property references message that is not defined: '{message_identifier}' in @ '{location}'"
                )
                continue

            message_model.correlation_properties = correlation_property_models  # type: ignore

    @classmethod
    def delete_all_message_models(cls) -> None:
        MessageModel.query.delete()

    @classmethod
    def delete_message_models_at_location(cls, location: str) -> None:
        MessageModel.query.filter_by(location=location).delete()

    @classmethod
    def save_all_message_models(cls, all_message_models: dict[tuple[str, str], MessageModel]) -> None:
        for message_model in all_message_models.values():
            db.session.add(message_model)

            for correlation_property_model in message_model.correlation_properties:
                db.session.add(correlation_property_model)
