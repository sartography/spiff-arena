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
        message_location = message_definition.get("location", process_group.id)
        message_id = message_definition.get("id")
        if isinstance(message_id, str) and message_id.isdigit():
            message_id = int(message_id)

        existing_model = MessageModel.query.filter_by(identifier=identifier, location=message_location).first()
        existing_message_id = existing_model.id if existing_model else None

        if message_id is not None:
            model_by_id = MessageModel.query.filter_by(id=message_id).first()
            if model_by_id is not None and model_by_id.identifier != identifier:
                raise ValueError(
                    f"Supplied message_id {message_id} belongs to a different message"
                    f" ('{model_by_id.identifier}' at '{model_by_id.location}')."
                    f" Cannot reuse this id for '{identifier}' at '{message_location}'."
                )
            resolved_message_id = message_id
        else:
            resolved_message_id = existing_message_id

        message_model = MessageModel(identifier=identifier, location=message_location, schema=schema)
        if resolved_message_id is not None:
            message_model.id = resolved_message_id

        return message_model

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
    def save_all_message_models(
        cls,
        all_message_models: dict[tuple[str, str], MessageModel],
        usage_map: dict[tuple[str, str], list[str]] | None = None,
    ) -> None:
        for message_model in all_message_models.values():
            correlation_property_models = list(message_model.correlation_properties)
            message_model_to_merge = MessageModel(
                identifier=message_model.identifier,
                location=message_model.location,
                schema=message_model.schema,
                process_model_identifiers=(
                    sorted(usage_map.get((message_model.identifier, message_model.location), []))
                    if usage_map
                    else None
                ),
            )
            if message_model.id is not None:
                message_model_to_merge.id = message_model.id

            merged_message_model: MessageModel = db.session.merge(message_model_to_merge)
            db.session.flush()

            MessageCorrelationPropertyModel.query.filter_by(message_id=merged_message_model.id).delete()
            for correlation_property_model in correlation_property_models:
                correlation_property_model.message_id = merged_message_model.id
                db.session.add(correlation_property_model)

    @classmethod
    def remove_process_model_from_usage(cls, process_model_id: str) -> None:
        """Remove a process model ID from process_model_identifiers on all MessageModels that reference it."""
        messages = MessageModel.query.filter(
            MessageModel.process_model_identifiers.isnot(None)  # type: ignore
        ).all()
        for message in messages:
            ids = list(message.process_model_identifiers or [])
            if process_model_id in ids:
                ids.remove(process_model_id)
                message.process_model_identifiers = ids
                db.session.add(message)

    @classmethod
    def remove_process_group_from_usage(cls, process_group_id: str) -> None:
        """Remove all process model IDs under a process group from process_model_identifiers."""
        prefix = process_group_id + "/"
        messages = MessageModel.query.filter(
            MessageModel.process_model_identifiers.isnot(None)  # type: ignore
        ).all()
        for message in messages:
            ids = list(message.process_model_identifiers or [])
            new_ids = [pm_id for pm_id in ids if pm_id != process_group_id and not pm_id.startswith(prefix)]
            if len(new_ids) != len(ids):
                message.process_model_identifiers = new_ids
                db.session.add(message)
