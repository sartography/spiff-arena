from time import time
from typing import Any

from SpiffWorkflow.bpmn.serializer.helpers.registry import BpmnConverter  # type: ignore
from SpiffWorkflow.bpmn.specs.data_spec import BpmnDataStoreSpecification  # type: ignore
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore

from spiffworkflow_backend.data_stores.crud import DataStoreCRUD
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.typeahead import TypeaheadModel


class TypeaheadDataStore(BpmnDataStoreSpecification, DataStoreCRUD):  # type: ignore
    """TypeaheadDataStore."""

    @staticmethod
    def existing_data_stores() -> list[dict[str, Any]]:
        data_stores = []

        keys = db.session.query(TypeaheadModel.category).distinct().order_by(TypeaheadModel.category).all()  # type: ignore
        for key in keys:
            data_stores.append({"name": key[0], "type": "typeahead", "identifier": key[0], "clz": "TypeaheadDataStore"})

        return data_stores

    @staticmethod
    def query_data_store(name: str) -> Any:
        return TypeaheadModel.query.filter_by(category=name).order_by(TypeaheadModel.category, TypeaheadModel.search_term)

    @staticmethod
    def build_response_item(model: Any) -> dict[str, Any]:
        result = model.result
        result["search_term"] = model.search_term
        return result  # type: ignore

    def get(self, my_task: SpiffTask) -> None:
        """get."""
        raise Exception("This is a write only data store.")

    def set(self, my_task: SpiffTask) -> None:
        """set."""
        typeahead_data_by_category = my_task.data[self.bpmn_id]
        for category, items in typeahead_data_by_category.items():
            db.session.query(TypeaheadModel).filter_by(category=category).delete()
            objects = [self._make_object(category, item) for item in items]
            db.session.bulk_save_objects(objects)
        db.session.commit()
        del my_task.data[self.bpmn_id]

    def _make_object(self, category: str, item: dict[str, Any]) -> TypeaheadModel:
        now = round(time())
        return TypeaheadModel(
            category=category,
            search_term=item["search_term"],
            result=item["result"],
            created_at_in_seconds=now,
            updated_at_in_seconds=now,
        )

    @staticmethod
    def register_data_store_class(data_store_classes: dict[str, Any]) -> None:
        data_store_classes["TypeaheadDataStore"] = TypeaheadDataStore


class TypeaheadDataStoreConverter(BpmnConverter):  # type: ignore
    """TypeaheadDataStoreConverter."""

    def to_dict(self, spec: Any) -> dict[str, Any]:
        """to_dict."""
        return {
            "bpmn_id": spec.bpmn_id,
            "bpmn_name": spec.bpmn_name,
            "capacity": spec.capacity,
            "is_unlimited": spec.is_unlimited,
        }

    def from_dict(self, dct: dict[str, Any]) -> TypeaheadDataStore:
        """from_dict."""
        return TypeaheadDataStore(**dct)
