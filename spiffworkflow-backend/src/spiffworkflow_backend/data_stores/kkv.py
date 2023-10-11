from typing import Any

from flask import current_app
from SpiffWorkflow.bpmn.serializer.helpers.spec import BpmnSpecConverter  # type: ignore
from SpiffWorkflow.bpmn.specs.data_spec import BpmnDataStoreSpecification  # type: ignore
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.json_data_store import JSONDataStoreModel
from spiffworkflow_backend.services.file_system_service import FileSystemService
from spiffworkflow_backend.services.reference_cache_service import ReferenceCacheService


class KKVDataStore(BpmnDataStoreSpecification):  # type: ignore
    """KKVDataStore."""

    def get(self, my_task: SpiffTask) -> None:
        """get."""
        def getter(k1: str, k2: str):
            return "some value"
        my_task.data[self.bpmn_id] = getter

    def set(self, my_task: SpiffTask) -> None:
        """set."""
        data = my_task.data[self.bpmn_id]
        del my_task.data[self.bpmn_id]

    @staticmethod
    def register_converter(spec_config: dict[str, Any]) -> None:
        spec_config["task_specs"].append(KKVDataStoreConverter)

    @staticmethod
    def register_data_store_class(data_store_classes: dict[str, Any]) -> None:
        data_store_classes["KKVDataStore"] = KKVDataStore


class KKVDataStoreConverter(BpmnSpecConverter):  # type: ignore
    """KKVDataStoreConverter."""

    def __init__(self, registry):  # type: ignore
        """__init__."""
        super().__init__(KKVDataStore, registry)

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

