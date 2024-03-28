from typing import Any

from flask import current_app
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore

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
