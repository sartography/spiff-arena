import os
from typing import Any

from flask import current_app

from spiffworkflow_backend.data_stores.json import JSONDataStore
from spiffworkflow_backend.data_stores.kkv import KKVDataStore
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.json_data_store import JSONDataStoreModel
from spiffworkflow_backend.models.kkv_data_store import KKVDataStoreModel
from spiffworkflow_backend.models.message_model import MessageModel
from spiffworkflow_backend.models.process_group import ProcessGroup
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.models.reference_cache import ReferenceCacheModel
from spiffworkflow_backend.services.file_system_service import FileSystemService
from spiffworkflow_backend.services.message_definition_service import MessageDefinitionService
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.reference_cache_service import ReferenceCacheService
from spiffworkflow_backend.services.spec_file_service import SpecFileService
from spiffworkflow_backend.services.upsearch_service import UpsearchService


class DataSetupService:
    @classmethod
    def run_setup(cls) -> list:
        return cls.refresh_process_model_caches()

    @classmethod
    def refresh_process_model_caches(cls) -> list:
        """Build a cache of all processes, messages, correlation keys, and start events.

        These all exist within processes located on the file system, so we can quickly reference them
        from the database.
        """
        current_app.logger.debug("DataSetupService.refresh_process_model_caches() start")

        failing_process_models = []
        files = FileSystemService.walk_files_from_root_path(True, None)
        reference_objects: dict[str, ReferenceCacheModel] = {}
        all_data_store_specifications: dict[tuple[str, str, str], Any] = {}
        all_message_models: dict[tuple[str, str], MessageModel] = {}
        references = []

        for file in files:
            if FileSystemService.is_process_model_json_file(file):
                process_model = ProcessModelService.get_process_model_from_path(file)
                # Use the common processing logic
                model_refs, model_failures = cls._extract_process_model_references(process_model, reference_objects)
                references.extend(model_refs)
                failing_process_models.extend(model_failures)
            elif FileSystemService.is_data_store_json_file(file):
                relative_location = FileSystemService.relative_location(file)
                file_name = os.path.basename(file)
                (identifier, _) = os.path.splitext(file_name)
                reference_cache = ReferenceCacheModel.from_params(
                    identifier,
                    identifier,
                    "data_store",
                    file_name,
                    relative_location,
                    None,
                    False,
                )
                ReferenceCacheService.add_unique_reference_cache_object(reference_objects, reference_cache)
            elif FileSystemService.is_process_group_json_file(file):
                try:
                    process_group = ProcessModelService.find_or_create_process_group(os.path.dirname(file))
                    cls._collect_data_store_specifications(process_group, file, all_data_store_specifications)
                    MessageDefinitionService.collect_message_models(process_group, process_group.id, all_message_models)
                except Exception:
                    current_app.logger.debug(f"Failed to load process group from file @ '{file}'")
                    continue

        current_app.logger.debug("DataSetupService.refresh_process_model_caches() end")
        ReferenceCacheService.add_new_generation(reference_objects)
        cls._sync_data_store_models_with_specifications(all_data_store_specifications)

        usage_map = cls._build_message_usage_map(references, all_message_models)
        MessageDefinitionService.delete_all_message_models()
        db.session.commit()
        MessageDefinitionService.save_all_message_models(all_message_models, usage_map)
        db.session.commit()

        cls._update_process_model_caches_for_references(references, failing_process_models)
        return failing_process_models

    @classmethod
    def refresh_single_process_model_cache(cls, process_model_id: str) -> list:
        current_app.logger.debug(f"DataSetupService.refresh_single_process_model_cache() start for {process_model_id}")

        failing_process_models = []
        reference_objects: dict[str, ReferenceCacheModel] = {}

        try:
            process_model = ProcessModelService.get_process_model(process_model_id)
            references, model_failures = cls._extract_process_model_references(process_model, reference_objects)
            failing_process_models.extend(model_failures)
            cls._update_process_model_caches_for_references(references, failing_process_models)
            cls._update_message_usage_for_process_model(process_model_id, references)
        except Exception as ex:
            failing_process_models.append((process_model_id, str(ex)))

        current_app.logger.debug(f"DataSetupService.refresh_single_process_model_cache() end for {process_model_id}")
        return failing_process_models

    @classmethod
    def _build_message_usage_map(
        cls, references: list, all_message_models: dict[tuple[str, str], Any]
    ) -> dict[tuple[str, str], list[str]]:
        """Build a map of (message_name, location) -> sorted list of process_model_ids that declare the message."""
        usage: dict[tuple[str, str], set[str]] = {}
        message_locations_by_identifier = cls._message_locations_by_identifier(all_message_models.keys())
        for ref in references:
            for msg_name in ref.messages:
                nearest_location = cls._find_nearest_message_location(
                    ref.relative_location, message_locations_by_identifier.get(msg_name, set())
                )
                if nearest_location is None:
                    continue
                usage.setdefault((msg_name, nearest_location), set()).add(ref.relative_location)
        return {k: sorted(v) for k, v in usage.items()}

    @classmethod
    def _update_message_usage_for_process_model(cls, process_model_id: str, references: list) -> None:
        """After a single-model refresh, update process_model_identifiers on affected MessageModels."""
        new_message_names = {msg_name for ref in references for msg_name in ref.messages}
        message_models = (
            MessageModel.query.filter(MessageModel.identifier.in_(new_message_names)).all()  # type: ignore
            if new_message_names
            else []
        )
        message_locations_by_identifier = cls._message_locations_by_identifier(
            (message_model.identifier, message_model.location) for message_model in message_models
        )
        message_models_by_key = {
            (message_model.identifier, message_model.location): message_model for message_model in message_models
        }

        # Remove this process model from all messages it's no longer in
        MessageDefinitionService.remove_process_model_from_usage(process_model_id)

        # Add it to messages it now declares
        for ref in references:
            for msg_name in ref.messages:
                nearest_location = cls._find_nearest_message_location(
                    ref.relative_location, message_locations_by_identifier.get(msg_name, set())
                )
                if nearest_location is None:
                    continue

                message = message_models_by_key.get((msg_name, nearest_location))
                if message is None:
                    continue

                ids = list(message.process_model_identifiers or [])
                if process_model_id in ids:
                    continue

                ids.append(process_model_id)
                message.process_model_identifiers = sorted(ids)
                db.session.add(message)
        db.session.commit()

    @classmethod
    def _message_locations_by_identifier(cls, message_model_keys: Any) -> dict[str, set[str]]:
        locations_by_identifier: dict[str, set[str]] = {}
        for identifier, location in message_model_keys:
            locations_by_identifier.setdefault(identifier, set()).add(location)
        return locations_by_identifier

    @classmethod
    def _find_nearest_message_location(cls, process_model_id: str, candidate_locations: set[str]) -> str | None:
        for location in UpsearchService.upsearch_locations(process_model_id):
            if location in candidate_locations:
                return location
        return None

    @classmethod
    def _collect_data_store_specifications(
        cls, process_group: ProcessGroup, file_name: str, all_data_store_specifications: dict[tuple[str, str, str], Any]
    ) -> None:
        for data_store_type, specs_by_id in process_group.data_store_specifications.items():
            if not isinstance(specs_by_id, dict):
                current_app.logger.debug(f"Expected dictionary as value for key '{data_store_type}' in file @ '{file_name}'")
                continue

            for identifier, specification in specs_by_id.items():
                location = specification.get("location")
                if location is None:
                    current_app.logger.debug(
                        f"Location missing from data store specification '{identifier}' in file @ '{file_name}'"
                    )
                    continue

                all_data_store_specifications[(data_store_type, location, identifier)] = specification

    @classmethod
    def _sync_data_store_models_with_specifications(cls, all_data_store_specifications: dict[tuple[str, str, str], Any]) -> None:
        all_data_store_models: dict[tuple[str, str, str], Any] = {}

        kkv_models = db.session.query(KKVDataStoreModel).all()
        json_models = db.session.query(JSONDataStoreModel).all()

        for kkv_model in kkv_models:
            all_data_store_models[("kkv", kkv_model.location, kkv_model.identifier)] = kkv_model

        for json_model in json_models:
            all_data_store_models[("json", json_model.location, json_model.identifier)] = json_model

        specification_keys = set(all_data_store_specifications.keys())
        model_keys = set(all_data_store_models.keys())

        #
        # At this point we have a dictionary of all data store specifications from all the process_group.json files and
        # a dictionary of all data store models. These two dictionaries use the same key format of (type, location, identifier)
        # which allows checking to see if a given data store has a specification and/or a model.
        #
        # With this we can perform set operations on the keys of the two dictionaries to figure out what needs to be
        # inserted, updated or deleted. If a key has a specification but not a model, an insert needs to happen. If a key
        # has a specification and a model, an update needs to happen. If a key has a model but no specification, a delete
        # needs to happen.
        #

        keys_to_insert = specification_keys - model_keys
        keys_to_update = specification_keys & model_keys
        keys_to_delete = model_keys - specification_keys

        current_app.logger.debug(f"DataSetupService: all_data_store_specifications: {all_data_store_specifications}")
        current_app.logger.debug(f"DataSetupService: all_data_store_models: {all_data_store_models}")
        current_app.logger.debug(f"DataSetupService: keys_to_insert: {keys_to_insert}")
        current_app.logger.debug(f"DataSetupService: keys_to_update: {keys_to_update}")
        current_app.logger.debug(f"DataSetupService: keys_to_delete: {keys_to_delete}")

        model_creators = {
            "kkv": KKVDataStore.create_instance,
            "json": JSONDataStore.create_instance,
        }

        def update_model_from_specification(model: Any, key: tuple[str, str, str]) -> None:
            specification = all_data_store_specifications.get(key)
            if specification is None:
                current_app.logger.debug(
                    f"DataSetupService: was expecting key '{key}' to point to a data store specification for model updating."
                )
                return

            name = specification.get("name")
            schema = specification.get("schema")

            if name is None or schema is None:
                current_app.logger.debug(
                    f"DataSetupService: was expecting key '{key}' to point to a valid data store specification for model"
                    " updating."
                )
                return

            model.name = name
            model.schema = schema
            model.description = specification.get("description")

        for key in keys_to_insert:
            data_store_type, location, identifier = key

            if data_store_type not in model_creators:
                current_app.logger.debug(f"DataSetupService: cannot create model for type '{data_store_type}'.")
                continue

            model = model_creators[data_store_type](identifier, location)
            update_model_from_specification(model, key)
            db.session.add(model)

        for key in keys_to_update:
            model = all_data_store_models.get(key)
            if model is None:
                current_app.logger.debug(
                    f"DataSetupService: was expecting key '{key}' to point to a data store model for model updating."
                )
                continue
            update_model_from_specification(model, key)

        for key in keys_to_delete:
            model = all_data_store_models.get(key)
            if model is None:
                current_app.logger.debug(f"DataSetupService: was expecting key '{key}' to point to a data store model to delete.")
                continue
            db.session.delete(model)

    @classmethod
    def _extract_process_model_references(
        cls, process_model: ProcessModelInfo, reference_objects: dict[str, ReferenceCacheModel]
    ) -> tuple[list, list]:
        failing_process_models = []
        references = []

        current_app.logger.debug(f"Extracting References for Process Model: {process_model.display_name}")

        try:
            refs = SpecFileService.get_references_for_process(process_model)
            for ref in refs:
                try:
                    reference_cache = ReferenceCacheModel.from_spec_reference(ref)
                    ReferenceCacheService.add_unique_reference_cache_object(reference_objects, reference_cache)
                    db.session.commit()
                    references.append(ref)
                except Exception as ex:
                    failing_process_models.append(
                        (
                            f"{ref.relative_location}/{ref.file_name}",
                            repr(ex),
                        )
                    )
        except Exception as ex2:
            failing_process_models.append(
                (
                    f"{process_model.id}",
                    str(ex2),
                )
            )

        return references, failing_process_models

    @classmethod
    def _update_process_model_caches_for_references(cls, references: list, failing_process_models: list) -> None:
        for ref in references:
            try:
                SpecFileService.update_caches_except_process(ref)
                db.session.commit()
            except Exception as ex:
                failing_process_models.append(
                    (
                        f"{ref.relative_location}/{ref.file_name}",
                        repr(ex),
                    )
                )
