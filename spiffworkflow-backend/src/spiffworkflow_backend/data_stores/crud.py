from typing import Any

import jsonschema
from flask import current_app
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore

from spiffworkflow_backend.models.json_data_store import JSONDataStoreModel
from spiffworkflow_backend.models.kkv_data_store import KKVDataStoreModel
from spiffworkflow_backend.services.upsearch_service import UpsearchService


class DataStoreReadError(Exception):
    pass


class DataStoreWriteError(Exception):
    pass


class DataStoreCRUD:
    @staticmethod
    def create_instance(identifier: str, location: str) -> Any:
        raise Exception("must implement")

    @staticmethod
    def existing_instance(identifier: str, location: str) -> Any:
        raise Exception("must implement")

    @classmethod
    def clear(cls, identifier: str, location: str | None) -> None:
        raise Exception("must implement")

    @classmethod
    def delete(cls, identifier: str, location: str | None) -> None:
        raise Exception("must implement")

    @staticmethod
    def existing_data_stores(process_group_identifiers: list[str] | None = None) -> list[dict[str, Any]]:
        raise Exception("must implement")

    @staticmethod
    def get_data_store_query(name: str, process_group_identifier: str | None) -> Any:
        raise Exception("must implement")

    @staticmethod
    def build_response_item(model: Any) -> dict[str, Any]:
        raise Exception("must implement")

    @staticmethod
    def create_record(name: str, data: dict[str, Any]) -> None:
        raise Exception("must implement")

    @staticmethod
    def update_record(name: str, data: dict[str, Any]) -> None:
        raise Exception("must implement")

    @staticmethod
    def delete_record(name: str, data: dict[str, Any]) -> None:
        raise Exception("must implement")

    @staticmethod
    def process_model_location_for_task(spiff_task: SpiffTask) -> str | None:
        from spiffworkflow_backend.models.reference_cache import ReferenceCacheModel

        # Try to find the location based on the process identifier (for called processes)
        if spiff_task.workflow.spec.name:
            reference = (
                ReferenceCacheModel.basic_query()
                .filter_by(identifier=spiff_task.workflow.spec.name, type="process")
                .first()
            )
            if reference:
                return reference.relative_location

        # Fallback to the old method (thread local data) - mostly for backward compatibility or edge cases
        tld = current_app.config.get("THREAD_LOCAL_DATA")
        if tld and hasattr(tld, "process_model_identifier"):
            return tld.process_model_identifier  # type: ignore
        return None

    @classmethod
    def data_store_location_for_task(cls, model: Any, spiff_task: SpiffTask, identifier: str) -> str | None:
        location = cls.process_model_location_for_task(spiff_task)
        if location is None:
            return None

        locations = UpsearchService.upsearch_locations(location)
        model = (
            model.query.filter_by(identifier=identifier)
            .filter(model.location.in_(locations))
            .order_by(model.location.desc())
            .first()
        )

        if model is None:
            return None

        return model.location  # type: ignore

    @classmethod
    def validate_schema(cls, store_model: KKVDataStoreModel | JSONDataStoreModel, value: dict) -> None:
        if store_model.schema:
            try:
                jsonschema.validate(
                    instance=value,
                    schema=store_model.schema,
                    format_checker=jsonschema.FormatChecker(),
                )
            except (jsonschema.exceptions.ValidationError, jsonschema.exceptions.SchemaError, TypeError) as e:
                raise DataStoreWriteError(
                    f"Attempting to write data that does not match the provided schema for '{store_model.identifier}': {e}"
                ) from e
