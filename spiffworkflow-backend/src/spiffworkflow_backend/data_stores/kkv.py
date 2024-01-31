from typing import Any

from SpiffWorkflow.bpmn.serializer.helpers import BpmnConverter  # type: ignore
from SpiffWorkflow.bpmn.specs.data_spec import BpmnDataStoreSpecification  # type: ignore
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore

from spiffworkflow_backend.data_stores.crud import DataStoreCRUD
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.kkv_data_store import KKVDataStoreModel


class KKVDataStore(BpmnDataStoreSpecification, DataStoreCRUD):  # type: ignore
    """KKVDataStore."""

    @staticmethod
    def existing_data_stores(process_group_identifier: str | None = None) -> list[dict[str, Any]]:
        data_stores: list[dict[str, Any]] = []

        if process_group_identifier is not None:
            # temporary until this data store gets location support
            return data_stores

        keys = (
            db.session.query(KKVDataStoreModel.top_level_key)
            .distinct()  # type: ignore
            .order_by(KKVDataStoreModel.top_level_key)
            .all()
        )
        for key in keys:
            data_stores.append({"name": key[0], "type": "kkv", "id": "", "clz": "KKVDataStore"})

        return data_stores

    @staticmethod
    def get_data_store_query(name: str, process_group_identifier: str | None) -> Any:
        return KKVDataStoreModel.query.filter_by(top_level_key=name).order_by(
            KKVDataStoreModel.top_level_key, KKVDataStoreModel.secondary_key
        )

    @staticmethod
    def build_response_item(model: Any) -> dict[str, Any]:
        return {
            "secondary_key": model.secondary_key,
            "value": model.value,
        }

    def _get_model(self, top_level_key: str, secondary_key: str) -> KKVDataStoreModel | None:
        model = db.session.query(KKVDataStoreModel).filter_by(top_level_key=top_level_key, secondary_key=secondary_key).first()
        return model

    def _delete_all_for_top_level_key(self, top_level_key: str) -> None:
        models = db.session.query(KKVDataStoreModel).filter_by(top_level_key=top_level_key).all()
        for model in models:
            db.session.delete(model)

    def get(self, my_task: SpiffTask) -> None:
        """get."""

        def getter(top_level_key: str, secondary_key: str) -> Any | None:
            model = self._get_model(top_level_key, secondary_key)
            if model is not None:
                return model.value
            return None

        my_task.data[self.bpmn_id] = getter

    def set(self, my_task: SpiffTask) -> None:
        """set."""
        data = my_task.data[self.bpmn_id]
        if not isinstance(data, dict):
            raise Exception(
                f"When writing to this data store, a dictionary is expected as the value for variable '{self.bpmn_id}'"
            )
        for top_level_key, second_level in data.items():
            if second_level is None:
                self._delete_all_for_top_level_key(top_level_key)
                continue
            if not isinstance(second_level, dict):
                raise Exception(
                    "When writing to this data store, a dictionary is expected as the value for"
                    f" '{self.bpmn_id}[\"{top_level_key}\"]'"
                )
            for secondary_key, value in second_level.items():
                model = self._get_model(top_level_key, secondary_key)
                if model is None and value is None:
                    continue
                if value is None:
                    db.session.delete(model)
                    continue
                if model is None:
                    model = KKVDataStoreModel(top_level_key=top_level_key, secondary_key=secondary_key, value=value)
                else:
                    model.value = value
                db.session.add(model)
        db.session.commit()
        del my_task.data[self.bpmn_id]

    @staticmethod
    def register_data_store_class(data_store_classes: dict[str, Any]) -> None:
        data_store_classes["KKVDataStore"] = KKVDataStore


class KKVDataStoreConverter(BpmnConverter):  # type: ignore
    """KKVDataStoreConverter."""

    def to_dict(self, spec: Any) -> dict[str, Any]:
        """to_dict."""
        return {
            "bpmn_id": spec.bpmn_id,
            "bpmn_name": spec.bpmn_name,
            "capacity": spec.capacity,
            "is_unlimited": spec.is_unlimited,
        }

    def from_dict(self, dct: dict[str, Any]) -> KKVDataStore:
        """from_dict."""
        return KKVDataStore(**dct)
