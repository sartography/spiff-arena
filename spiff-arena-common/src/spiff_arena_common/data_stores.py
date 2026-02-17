from SpiffWorkflow.bpmn.serializer.helpers import BpmnConverter
from SpiffWorkflow.bpmn.specs.data_spec import BpmnDataStoreSpecification


class DataStoreReadError(Exception):
    pass


class DataStoreWriteError(Exception):
    pass

class JSONFileDataStore(BpmnDataStoreSpecification):
    def get(self, my_task):
        contents, err = self.delegate.get(self.bpmn_id, my_task)
        if err is not None:
            raise DataStoreReadError(f"Unable to read from data store '{self.bpmn_id}': {err}")
        my_task.data[self.bpmn_id] = contents

    def set(self, my_task):
        if self.bpmn_id not in my_task.data:
            return
        data = my_task.data[self.bpmn_id]
        err = self.delegate.set(self.bpmn_id, my_task, data)
        if err is not None:
            raise DataStoreWriteError(f"Unable to write to data store '{self.bpmn_id}': {err}")
        del my_task.data[self.bpmn_id]

class JSONFileDataStoreConverter(BpmnConverter):
    def to_dict(self, spec):
        return {
            "bpmn_id": spec.bpmn_id,
            "bpmn_name": spec.bpmn_name,
            "capacity": spec.capacity,
            "is_unlimited": spec.is_unlimited,
        }

    def from_dict(self, dct):
        return JSONFileDataStore(**dct)
