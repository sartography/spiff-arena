from typing import Any

import jsonschema  # type: ignore
from SpiffWorkflow.bpmn.serializer.helpers import BpmnConverter  # type: ignore
from SpiffWorkflow.bpmn.specs.data_spec import BpmnDataStoreSpecification  # type: ignore
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore

from spiffworkflow_backend.data_stores.crud import DataStoreCRUD
from spiffworkflow_backend.data_stores.crud import DataStoreReadError
from spiffworkflow_backend.data_stores.crud import DataStoreWriteError
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.kkv_data_store import KKVDataStoreModel
from spiffworkflow_backend.models.kkv_data_store_entry import KKVDataStoreEntryModel


class KKVDataStore(BpmnDataStoreSpecification, DataStoreCRUD):  # type: ignore
    @staticmethod
    def create_instance(identifier: str, location: str) -> Any:
        return KKVDataStoreModel(
            identifier=identifier,
            location=location,
        )

    @staticmethod
    def existing_instance(identifier: str, location: str) -> Any:
        return db.session.query(KKVDataStoreModel).filter_by(identifier=identifier, location=location).first()

    @staticmethod
    def existing_data_stores(process_group_identifiers: list[str] | None = None) -> list[dict[str, Any]]:
        data_stores = []

        query = db.session.query(KKVDataStoreModel)
        if process_group_identifiers:
            query = query.filter(KKVDataStoreModel.location.in_(process_group_identifiers))  # type: ignore
        models = query.order_by(KKVDataStoreModel.name).all()
        for model in models:
            data_stores.append(
                {"name": model.name, "type": "kkv", "id": model.identifier, "clz": "KKVDataStore", "location": model.location}
            )

        return data_stores

    @staticmethod
    def get_data_store_query(identifier: str, process_group_identifier: str | None) -> Any:
        query = KKVDataStoreModel.query
        if process_group_identifier is not None:
            query = query.filter_by(identifier=identifier, location=process_group_identifier)
        else:
            query = query.filter_by(name=identifier)
        return query.order_by(KKVDataStoreModel.name)

    @staticmethod
    def build_response_item(model: Any) -> dict[str, Any]:
        data = []

        for entry in model.entries:
            data.append(
                {
                    "top_level_key": entry.top_level_key,
                    "secondary_key": entry.secondary_key,
                    "value": entry.value,
                }
            )

        return {
            "data": data,
        }

    @classmethod
    def add_data_store_getters_to_spiff_task(cls, spiff_task: SpiffTask) -> None:
        """Adds the data store getters onto the task if necessary.

        This is because the getters are methods and methods are stripped out of task data when we serialize.
        These methods are added to task data when the task is marked as READY and therefore may not be there
        when the task actually runs.
        """
        data_input_associations = spiff_task.task_spec.data_input_associations
        for dia in data_input_associations:
            if isinstance(dia, KKVDataStore):
                dia.get(spiff_task)

    def get(self, my_task: SpiffTask) -> None:
        def getter(top_level_key: str, secondary_key: str | None) -> Any | None:
            location = self.data_store_location_for_task(KKVDataStoreModel, my_task, self.bpmn_id)
            store_model: KKVDataStoreModel | None = None

            if location is not None:
                store_model = db.session.query(KKVDataStoreModel).filter_by(identifier=self.bpmn_id, location=location).first()

            if store_model is None:
                raise DataStoreReadError(f"Unable to locate kkv data store '{self.bpmn_id}'.")

            if secondary_key is not None:
                model = (
                    db.session.query(KKVDataStoreEntryModel)
                    .filter_by(kkv_data_store_id=store_model.id, top_level_key=top_level_key, secondary_key=secondary_key)
                    .first()
                )

                if model is not None:
                    return model.value
                return None

            models = (
                db.session.query(KKVDataStoreEntryModel)
                .filter_by(kkv_data_store_id=store_model.id, top_level_key=top_level_key)
                .all()
            )

            values = {model.secondary_key: model.value for model in models}

            return values

        my_task.data[self.bpmn_id] = getter

    def set(self, my_task: SpiffTask) -> None:
        if self.bpmn_id not in my_task.data:
            return
        location = self.data_store_location_for_task(KKVDataStoreModel, my_task, self.bpmn_id)
        store_model: KKVDataStoreModel | None = None

        if location is not None:
            store_model = db.session.query(KKVDataStoreModel).filter_by(identifier=self.bpmn_id, location=location).first()

        if store_model is None:
            raise DataStoreWriteError(f"Unable to locate kkv data store '{self.bpmn_id}'.")

        data = my_task.data[self.bpmn_id]

        if not isinstance(data, dict):
            raise DataStoreWriteError(
                f"When writing to this data store, a dictionary is expected as the value for variable '{self.bpmn_id}'"
            )
        for top_level_key, second_level in data.items():
            if second_level is None:
                models = (
                    db.session.query(KKVDataStoreEntryModel)
                    .filter_by(kkv_data_store_id=store_model.id, top_level_key=top_level_key)
                    .all()
                )
                for model_to_delete in models:
                    db.session.delete(model_to_delete)
                continue
            if not isinstance(second_level, dict):
                raise DataStoreWriteError(
                    "When writing to this data store, a dictionary is expected as the value for"
                    f" '{self.bpmn_id}[\"{top_level_key}\"]'"
                )
            for secondary_key, value in second_level.items():
                model = (
                    db.session.query(KKVDataStoreEntryModel)
                    .filter_by(kkv_data_store_id=store_model.id, top_level_key=top_level_key, secondary_key=secondary_key)
                    .first()
                )

                if model is None and value is None:
                    continue
                if value is None:
                    db.session.delete(model)
                    continue

                try:
                    jsonschema.validate(instance=value, schema=store_model.schema)
                except jsonschema.exceptions.ValidationError as e:
                    raise DataStoreWriteError(
                        f"Attempting to write data that does not match the provided schema for '{self.bpmn_id}': {e}"
                    ) from e

                if model is None:
                    model = KKVDataStoreEntryModel(
                        kkv_data_store_id=store_model.id,
                        top_level_key=top_level_key,
                        secondary_key=secondary_key,
                        value=value,
                    )
                else:
                    model.value = value
                db.session.add(model)
        db.session.commit()
        del my_task.data[self.bpmn_id]

    @staticmethod
    def register_data_store_class(data_store_classes: dict[str, Any]) -> None:
        data_store_classes["KKVDataStore"] = KKVDataStore


class KKVDataStoreConverter(BpmnConverter):  # type: ignore
    def to_dict(self, spec: Any) -> dict[str, Any]:
        return {
            "bpmn_id": spec.bpmn_id,
            "bpmn_name": spec.bpmn_name,
            "capacity": spec.capacity,
            "is_unlimited": spec.is_unlimited,
        }

    def from_dict(self, dct: dict[str, Any]) -> KKVDataStore:
        return KKVDataStore(**dct)
