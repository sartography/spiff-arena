from typing import Any

from flask import current_app
from SpiffWorkflow.bpmn.serializer.helpers.registry import BpmnConverter  # type: ignore
from SpiffWorkflow.bpmn.specs.data_spec import BpmnDataStoreSpecification  # type: ignore
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore

from spiffworkflow_backend.data_stores.crud import DataStoreCRUD
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.json_data_store import JSONDataStoreModel
from spiffworkflow_backend.services.file_system_service import FileSystemService
from spiffworkflow_backend.services.reference_cache_service import ReferenceCacheService


def _process_model_location_for_task(spiff_task: SpiffTask) -> str | None:
    tld = current_app.config.get("THREAD_LOCAL_DATA")
    if tld and hasattr(tld, "process_model_identifier"):
        return tld.process_model_identifier  # type: ignore
    return None


def _data_store_filename(name: str) -> str:
    return f"{name}.json"


def _data_store_exists_at_location(location: str, name: str) -> bool:
    return FileSystemService.file_exists_at_relative_path(location, _data_store_filename(name))


def _data_store_location_for_task(spiff_task: SpiffTask, name: str) -> str | None:
    location = _process_model_location_for_task(spiff_task)
    if location is None:
        return None
    if _data_store_exists_at_location(location, name):
        return location
    location = ReferenceCacheService.upsearch(location, name, "data_store")
    if location is None or not _data_store_exists_at_location(location, name):
        return None
    return location


class JSONDataStore(BpmnDataStoreSpecification, DataStoreCRUD):  # type: ignore
    """JSONDataStore."""

    @staticmethod
    def existing_data_stores() -> list[dict[str, Any]]:
        data_stores = []

        keys = db.session.query(JSONDataStoreModel.name).distinct().order_by(JSONDataStoreModel.name)  # type: ignore
        for key in keys:
            data_stores.append({"name": key[0], "type": "json"})

        return data_stores

    @staticmethod
    def query_data_store(name: str) -> Any:
        return JSONDataStoreModel.query.filter_by(name=name).order_by(JSONDataStoreModel.name)

    @staticmethod
    def build_response_item(model: Any) -> dict[str, Any]:
        return {"location": model.location, "data": model.data}

    def get(self, my_task: SpiffTask) -> None:
        """get."""
        model: JSONDataStoreModel | None = None
        location = _data_store_location_for_task(my_task, self.bpmn_id)
        if location is not None:
            model = db.session.query(JSONDataStoreModel).filter_by(name=self.bpmn_id, location=location).first()
        if model is None:
            raise Exception(f"Unable to read from data store '{self.bpmn_id}' using location '{location}'.")
        my_task.data[self.bpmn_id] = model.data

    def set(self, my_task: SpiffTask) -> None:
        """set."""
        location = _data_store_location_for_task(my_task, self.bpmn_id)
        if location is None:
            raise Exception(f"Unable to write to data store '{self.bpmn_id}' using location '{location}'.")
        data = my_task.data[self.bpmn_id]
        model = JSONDataStoreModel(
            name=self.bpmn_id,
            location=location,
            data=data,
        )

        db.session.query(JSONDataStoreModel).filter_by(name=self.bpmn_id, location=location).delete()
        db.session.add(model)
        db.session.commit()
        del my_task.data[self.bpmn_id]

    @staticmethod
    def register_data_store_class(data_store_classes: dict[str, Any]) -> None:
        data_store_classes["JSONDataStore"] = JSONDataStore


class JSONDataStoreConverter(BpmnConverter):  # type: ignore
    """JSONDataStoreConverter."""

    def to_dict(self, spec: Any) -> dict[str, Any]:
        """to_dict."""
        return {
            "bpmn_id": spec.bpmn_id,
            "bpmn_name": spec.bpmn_name,
            "capacity": spec.capacity,
            "is_unlimited": spec.is_unlimited,
        }

    def from_dict(self, dct: dict[str, Any]) -> JSONDataStore:
        """from_dict."""
        return JSONDataStore(**dct)


class JSONFileDataStore(BpmnDataStoreSpecification):  # type: ignore
    """JSONFileDataStore."""

    def get(self, my_task: SpiffTask) -> None:
        """get."""
        location = _data_store_location_for_task(my_task, self.bpmn_id)
        if location is None:
            raise Exception(f"Unable to read from data store '{self.bpmn_id}' using location '{location}'.")
        contents = FileSystemService.contents_of_json_file_at_relative_path(location, _data_store_filename(self.bpmn_id))
        my_task.data[self.bpmn_id] = contents

    def set(self, my_task: SpiffTask) -> None:
        """set."""
        location = _data_store_location_for_task(my_task, self.bpmn_id)
        if location is None:
            raise Exception(f"Unable to write to data store '{self.bpmn_id}' using location '{location}'.")
        data = my_task.data[self.bpmn_id]
        FileSystemService.write_to_json_file_at_relative_path(location, _data_store_filename(self.bpmn_id), data)
        del my_task.data[self.bpmn_id]

    @staticmethod
    def register_data_store_class(data_store_classes: dict[str, Any]) -> None:
        data_store_classes["JSONFileDataStore"] = JSONFileDataStore


class JSONFileDataStoreConverter(BpmnConverter):  # type: ignore
    """JSONFileDataStoreConverter."""

    def to_dict(self, spec: Any) -> dict[str, Any]:
        """to_dict."""
        return {
            "bpmn_id": spec.bpmn_id,
            "bpmn_name": spec.bpmn_name,
            "capacity": spec.capacity,
            "is_unlimited": spec.is_unlimited,
        }

    def from_dict(self, dct: dict[str, Any]) -> JSONFileDataStore:
        """from_dict."""
        return JSONFileDataStore(**dct)
