from typing import Any

import jsonschema  # type: ignore
from flask import current_app
from SpiffWorkflow.bpmn.serializer.helpers.registry import BpmnConverter  # type: ignore
from SpiffWorkflow.bpmn.specs.data_spec import BpmnDataStoreSpecification  # type: ignore
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore

from spiffworkflow_backend.data_stores.crud import DataStoreCRUD
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.json_data_store import JSONDataStoreModel
from spiffworkflow_backend.services.file_system_service import FileSystemService
from spiffworkflow_backend.services.reference_cache_service import ReferenceCacheService
from spiffworkflow_backend.services.upsearch_service import UpsearchService


class DataStoreReadError(Exception):
    pass


class DataStoreWriteError(Exception):
    pass


def _process_model_location_for_task(spiff_task: SpiffTask) -> str | None:
    tld = current_app.config.get("THREAD_LOCAL_DATA")
    if tld and hasattr(tld, "process_model_identifier"):
        return tld.process_model_identifier  # type: ignore
    return None


class JSONDataStore(BpmnDataStoreSpecification, DataStoreCRUD):  # type: ignore
    """JSONDataStore."""

    @staticmethod
    def create_instance(name: str, identifier: str, location: str, schema: dict[str, Any], description: str | None) -> None:
        model = JSONDataStoreModel(
            name=name,
            identifier=identifier,
            location=location,
            schema=schema,
            description=description or "",
            data={},
        )
        db.session.add(model)
        db.session.commit()

    @staticmethod
    def existing_data_stores() -> list[dict[str, Any]]:
        data_stores = []

        keys = db.session.query(JSONDataStoreModel.name).distinct().order_by(JSONDataStoreModel.name).all()  # type: ignore
        for key in keys:
            data_stores.append({"name": key[0], "type": "json"})

        return data_stores

    @staticmethod
    def query_data_store(name: str) -> Any:
        return JSONDataStoreModel.query.filter_by(name=name).order_by(JSONDataStoreModel.name)

    @staticmethod
    def build_response_item(model: Any) -> dict[str, Any]:
        return {"location": model.location, "identifier": model.identifier, "data": model.data}

    def get(self, my_task: SpiffTask) -> None:
        """get."""
        model: JSONDataStoreModel | None = None
        location = self._data_store_location_for_task(my_task, self.bpmn_id)
        if location is not None:
            model = db.session.query(JSONDataStoreModel).filter_by(identifier=self.bpmn_id, location=location).first()
        if model is None:
            raise DataStoreReadError(f"Unable to read from data store '{self.bpmn_id}' using location '{location}'.")
        my_task.data[self.bpmn_id] = model.data

    def set(self, my_task: SpiffTask) -> None:
        """set."""
        model: JSONDataStoreModel | None = None
        location = self._data_store_location_for_task(my_task, self.bpmn_id)

        if location is not None:
            model = JSONDataStoreModel.query.filter_by(identifier=self.bpmn_id, location=location).first()
        if location is None or model is None:
            raise DataStoreWriteError(f"Unable to write to data store '{self.bpmn_id}' using location '{location}'.")

        data = my_task.data[self.bpmn_id]

        try:
            jsonschema.validate(instance=data, schema=model.schema)
        except jsonschema.exceptions.ValidationError as e:
            raise DataStoreWriteError(
                f"Attempting to write data that does not match the provided schema for '{self.bpmn_id}': {e}"
            ) from e

        # TODO: validate data against schema
        model.data = data

        db.session.add(model)
        db.session.commit()
        del my_task.data[self.bpmn_id]

    def _data_store_location_for_task(self, spiff_task: SpiffTask, identifier: str) -> str | None:
        location = _process_model_location_for_task(spiff_task)
        if location is None:
            return None

        locations = UpsearchService.upsearch_locations(location)
        model = (
            JSONDataStoreModel.query.filter_by(identifier=identifier)
            .filter(JSONDataStoreModel.location.in_(locations))  # type: ignore
            .order_by(JSONDataStoreModel.location.desc())  # type: ignore
            .first()
        )

        if model is None:
            return None

        return model.location  # type: ignore

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
        location = self._data_store_location_for_task(my_task, self.bpmn_id)
        if location is None:
            raise DataStoreReadError(f"Unable to read from data store '{self.bpmn_id}' using location '{location}'.")
        contents = FileSystemService.contents_of_json_file_at_relative_path(location, self._data_store_filename(self.bpmn_id))
        my_task.data[self.bpmn_id] = contents

    def set(self, my_task: SpiffTask) -> None:
        """set."""
        location = self._data_store_location_for_task(my_task, self.bpmn_id)
        if location is None:
            raise DataStoreWriteError(f"Unable to write to data store '{self.bpmn_id}' using location '{location}'.")
        data = my_task.data[self.bpmn_id]
        FileSystemService.write_to_json_file_at_relative_path(location, self._data_store_filename(self.bpmn_id), data)
        del my_task.data[self.bpmn_id]

    def _data_store_location_for_task(self, spiff_task: SpiffTask, identifier: str) -> str | None:
        location = _process_model_location_for_task(spiff_task)
        if location is None:
            return None
        if self._data_store_exists_at_location(location, identifier):
            return location
        location = ReferenceCacheService.upsearch(location, identifier, "data_store")
        if location is None:
            return None
        if not self._data_store_exists_at_location(location, identifier):
            return None
        return location

    def _data_store_exists_at_location(self, location: str, identifier: str) -> bool:
        return FileSystemService.file_exists_at_relative_path(location, self._data_store_filename(identifier))

    def _data_store_filename(self, name: str) -> str:
        return f"{name}.json"

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
