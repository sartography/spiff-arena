from typing import Any

from SpiffWorkflow.bpmn.specs.data_spec import BpmnDataStoreSpecification  # type: ignore

from spiffworkflow_backend.data_stores.json import JSONDataStore
from spiffworkflow_backend.data_stores.json import JSONFileDataStore
from spiffworkflow_backend.data_stores.kkv import KKVDataStore
from spiffworkflow_backend.data_stores.typeahead import TypeaheadDataStore

DATA_STORES: list[BpmnDataStoreSpecification] = [
    KKVDataStore,
    JSONDataStore,
    JSONFileDataStore,
    TypeaheadDataStore,
]


def register_data_store_classes(data_store_classes: dict[str, Any]) -> None:
    for ds in DATA_STORES:
        ds.register_data_store_class(data_store_classes)
