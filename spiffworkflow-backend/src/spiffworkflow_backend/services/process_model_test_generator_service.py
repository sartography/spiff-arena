import copy

from SpiffWorkflow.bpmn.serializer.workflow import BpmnWorkflowSerializer  # type: ignore
from SpiffWorkflow.bpmn.specs.mixins import ServiceTaskMixin  # type: ignore
from SpiffWorkflow.spiff.serializer.config import SPIFF_CONFIG  # type: ignore


class ProcessModelTestGeneratorService:
    @classmethod
    def generate_test_from_process_instance_dict(
        cls, process_instance_dict: dict, test_case_identifier: str = "auto_generated_test_case"
    ) -> dict:
        wf_spec_converter = BpmnWorkflowSerializer.configure(SPIFF_CONFIG)
        serializer = BpmnWorkflowSerializer(wf_spec_converter)
        process_instance_dict_copy = copy.deepcopy(process_instance_dict)
        bpmn_process_instance = serializer.from_dict(process_instance_dict_copy)

        human_tasks = bpmn_process_instance.get_tasks(manual=True)
        service_tasks = bpmn_process_instance.get_tasks(spec_class=ServiceTaskMixin)
        all_spiff_tasks = human_tasks + service_tasks
        bpmn_unit_test_specification = {"tasks": {}, "expected_output_json": bpmn_process_instance.data}
        for spiff_task in all_spiff_tasks:
            process_id = spiff_task.workflow.spec.name
            bpmn_task_identifier = f"{process_id}:{spiff_task.task_spec.bpmn_id}"
            if bpmn_task_identifier not in bpmn_unit_test_specification["tasks"]:
                bpmn_unit_test_specification["tasks"][bpmn_task_identifier] = {}
            if "data" not in bpmn_unit_test_specification["tasks"][bpmn_task_identifier]:
                bpmn_unit_test_specification["tasks"][bpmn_task_identifier]["data"] = []

            previous_task_data = spiff_task.parent.data
            current_task_data = spiff_task.data
            cls.remove_duplicates(previous_task_data, current_task_data)
            bpmn_unit_test_specification["tasks"][bpmn_task_identifier]["data"].append(current_task_data)

        return {test_case_identifier: bpmn_unit_test_specification}

    @classmethod
    def remove_duplicates(cls, dict_one: dict, dict_two: dict) -> None:
        for key in list(dict_two.keys()):
            if key in dict_one:
                if isinstance(dict_one[key], dict) and isinstance(dict_two[key], dict):
                    cls.remove_duplicates(dict_one[key], dict_two[key])
                    if not dict_two[key]:
                        del dict_two[key]
                else:
                    del dict_two[key]
