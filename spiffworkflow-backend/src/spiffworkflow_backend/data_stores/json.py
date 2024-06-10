from typing import Any

import jsonschema  # type: ignore
from SpiffWorkflow.bpmn.serializer.helpers import BpmnConverter  # type: ignore
from SpiffWorkflow.bpmn.specs.data_spec import BpmnDataStoreSpecification  # type: ignore
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore

from spiffworkflow_backend.data_stores.crud import DataStoreCRUD
from spiffworkflow_backend.data_stores.crud import DataStoreReadError
from spiffworkflow_backend.data_stores.crud import DataStoreWriteError
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.json_data_store import JSONDataStoreModel
from spiffworkflow_backend.services.file_system_service import FileSystemService
from spiffworkflow_backend.services.reference_cache_service import ReferenceCacheService


class JSONDataStore(BpmnDataStoreSpecification, DataStoreCRUD):  # type: ignore
    """JSONDataStore."""

    @staticmethod
    def create_instance(identifier: str, location: str) -> Any:
        return JSONDataStoreModel(
            identifier=identifier,
            location=location,
            data={},
        )

    @staticmethod
    def existing_instance(identifier: str, location: str) -> Any:
        return db.session.query(JSONDataStoreModel).filter_by(identifier=identifier, location=location).first()

    @staticmethod
    def existing_data_stores(process_group_identifiers: list[str] | None = None) -> list[dict[str, Any]]:
        data_stores = []

        query = db.session.query(JSONDataStoreModel.name, JSONDataStoreModel.identifier, JSONDataStoreModel.location)
        if process_group_identifiers:
            query = query.filter(JSONDataStoreModel.location.in_(process_group_identifiers))  # type: ignore
        keys = query.order_by(JSONDataStoreModel.name).all()
        for key in keys:
            data_stores.append({"name": key[0], "type": "json", "id": key[1], "clz": "JSONDataStore", "location": key[2]})

        return data_stores

    @staticmethod
    def get_data_store_query(identifier: str, process_group_identifier: str | None) -> Any:
        query = JSONDataStoreModel.query
        if process_group_identifier is not None:
            query = query.filter_by(identifier=identifier, location=process_group_identifier)
        else:
            query = query.filter_by(name=identifier)
        return query.order_by(JSONDataStoreModel.name)

    @staticmethod
    def build_response_item(model: Any) -> dict[str, Any]:
        return {"data": model.data}

    def get(self, my_task: SpiffTask) -> None:
        """get."""
        model: JSONDataStoreModel | None = None
        location = self.data_store_location_for_task(JSONDataStoreModel, my_task, self.bpmn_id)

        if location is not None:
            model = db.session.query(JSONDataStoreModel).filter_by(identifier=self.bpmn_id, location=location).first()
        if model is None:
            raise DataStoreReadError(f"Unable to read from data store '{self.bpmn_id}' using location '{location}'.")

        my_task.data[self.bpmn_id] = model.data

    def set(self, my_task: SpiffTask) -> None:
        """set."""
        if self.bpmn_id not in my_task.data:
            return
        model: JSONDataStoreModel | None = None
        location = self.data_store_location_for_task(JSONDataStoreModel, my_task, self.bpmn_id)

        if location is not None:
            model = JSONDataStoreModel.query.filter_by(identifier=self.bpmn_id, location=location).first()
        if model is None:
            raise DataStoreWriteError(f"Unable to write to data store '{self.bpmn_id}' using location '{location}'.")

        data = my_task.data[self.bpmn_id]

        try:
            jsonschema.validate(instance=data, schema=model.schema)
        except jsonschema.exceptions.ValidationError as e:
            raise DataStoreWriteError(
                f"Attempting to write data that does not match the provided schema for '{self.bpmn_id}': {e}"
            ) from e

        model.data = data

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
        location = self._data_store_location_for_task(my_task, self.bpmn_id)
        if location is None:
            raise DataStoreReadError(f"Unable to read from data store '{self.bpmn_id}' using location '{location}'.")
        contents = FileSystemService.contents_of_json_file_at_relative_path(location, self._data_store_filename(self.bpmn_id))
        my_task.data[self.bpmn_id] = contents

    def set(self, my_task: SpiffTask) -> None:
        """set."""
        if self.bpmn_id not in my_task.data:
            return
        location = self._data_store_location_for_task(my_task, self.bpmn_id)
        if location is None:
            raise DataStoreWriteError(f"Unable to write to data store '{self.bpmn_id}' using location '{location}'.")
        data = my_task.data[self.bpmn_id]
        FileSystemService.write_to_json_file_at_relative_path(location, self._data_store_filename(self.bpmn_id), data)
        del my_task.data[self.bpmn_id]

    def _data_store_location_for_task(self, spiff_task: SpiffTask, identifier: str) -> str | None:
        location = DataStoreCRUD.process_model_location_for_task(spiff_task)
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
