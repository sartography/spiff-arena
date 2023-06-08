from SpiffWorkflow.bpmn.serializer.helpers.spec import BpmnSpecConverter
from SpiffWorkflow.bpmn.specs.data_spec import BpmnDataStoreSpecification
from spiffworkflow_backend.services.user_service import UserService
from typing import Any

class TypeaheadDataStore(BpmnDataStoreSpecification):
    """TypeaheadDataStore."""

    def get(self, my_task):
        """get."""
        assert self.bpmn_id == "employees_for_typeahead"
        my_task.data[self.bpmn_id] = "tmp"

    def set(self, my_task):
        """set."""
        assert self.bpmn_id == "employees_for_typeahead"
        tmp = my_task.data[self.bpmn_id]
        del my_task.data[self.bpmn_id]

    @staticmethod
    def register_converter(spec_config: dict[str, Any]):
        spec_config["task_specs"].append(TypeaheadDataStoreConverter)
        
    @staticmethod
    def register_data_store_class(data_store_classes: dict[str, Any]):
        data_store_classes["TypeaheadDataStore"] = TypeaheadDataStore
        # TODO: tmp
        data_store_classes["SomeDataStore"] = TypeaheadDataStore


class TypeaheadDataStoreConverter(BpmnSpecConverter):
    """TypeaheadDataStoreConverter."""

    def __init__(self, registry):
        """__init__."""
        super().__init__(TypeaheadDataStore, registry)

    def to_dict(self, spec):
        """to_dict."""
        return {
            "bpmn_id": spec.bpmn_id,
            "bpmn_name": spec.bpmn_name,
            "capacity": spec.capacity,
            "is_unlimited": spec.is_unlimited,
        }

    def from_dict(self, dct):
        """from_dict."""
        return TypeaheadDataStore(**dct)

    
