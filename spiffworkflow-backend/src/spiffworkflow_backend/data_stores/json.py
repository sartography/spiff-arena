from typing import Any

from flask import current_app
from SpiffWorkflow.bpmn.serializer.helpers.spec import BpmnSpecConverter  # type: ignore
from SpiffWorkflow.bpmn.specs.data_spec import BpmnDataStoreSpecification  # type: ignore
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.json_data_store import JSONDataStoreModel


def _process_model_location_for_task(spiff_task: SpiffTask) -> str | None:
    tld = current_app.config.get("THREAD_LOCAL_DATA")
    if tld and hasattr(tld, "process_model_identifier"):
        return tld.process_model_identifier  # type: ignore
    return None


class JSONDataStore(BpmnDataStoreSpecification):  # type: ignore
    """JSONDataStore."""

    def get(self, my_task: SpiffTask) -> None:
        """get."""
        model: JSONDataStoreModel | None = None
        location = _process_model_location_for_task(my_task)
        if location is not None:
            model = db.session.query(JSONDataStoreModel).filter_by(name=self.bpmn_id, location=location).first()
        if model is None:
            raise Exception(f"Unable to read from data store '{self.bpmn_id}' using location '{location}'.")
        my_task.data[self.bpmn_id] = model.data

    def set(self, my_task: SpiffTask) -> None:
        """set."""
        location = _process_model_location_for_task(my_task)
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
    def register_converter(spec_config: dict[str, Any]) -> None:
        spec_config["task_specs"].append(JSONDataStoreConverter)

    @staticmethod
    def register_data_store_class(data_store_classes: dict[str, Any]) -> None:
        data_store_classes["JSONDataStore"] = JSONDataStore


class JSONDataStoreConverter(BpmnSpecConverter):  # type: ignore
    """JSONDataStoreConverter."""

    def __init__(self, registry):  # type: ignore
        """__init__."""
        super().__init__(JSONDataStore, registry)

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
