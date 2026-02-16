from SpiffWorkflow.bpmn.serializer.helpers import BpmnConverter
from SpiffWorkflow.bpmn.specs.data_spec import BpmnDataStoreSpecification


class JSONFileDataStore(BpmnDataStoreSpecification):
    def get(self, my_task):
        #location = self._data_store_location_for_task(my_task, self.bpmn_id)
        #if location is None:
        #    raise DataStoreReadError(f"Unable to read from data store '{self.bpmn_id}' using location '{location}'.")
        #contents = FileSystemService.contents_of_json_file_at_relative_path(location, self._data_store_filename(self.bpmn_id))
        contents = {}
        my_task.data[self.bpmn_id] = contents

    def set(self, my_task):
        if self.bpmn_id not in my_task.data:
            return
        #location = self._data_store_location_for_task(my_task, self.bpmn_id)
        #if location is None:
        #    raise DataStoreWriteError(f"Unable to write to data store '{self.bpmn_id}' using location '{location}'.")
        #data = my_task.data[self.bpmn_id]
        #FileSystemService.write_to_json_file_at_relative_path(location, self._data_store_filename(self.bpmn_id), data)
        del my_task.data[self.bpmn_id]

    @staticmethod
    def register_data_store_class(data_store_classes):
        data_store_classes["JSONFileDataStore"] = JSONFileDataStore


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
