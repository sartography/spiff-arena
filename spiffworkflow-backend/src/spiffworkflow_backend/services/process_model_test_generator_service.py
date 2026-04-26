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

        # Build a mapping of task guid -> delta updates from the serialized dict.
        # The serializer already computes what data each task added vs its parent,
        # so we use that directly instead of deserializing and comparing parent/child data.
        task_deltas: dict[str, dict] = {}
        for guid, task_dict in process_instance_dict.get("tasks", {}).items():
            delta = task_dict.get("delta", {})
            task_deltas[guid] = delta.get("updates", {})
        for _sub_guid, sub_dict in process_instance_dict.get("subprocesses", {}).items():
            for guid, task_dict in sub_dict.get("tasks", {}).items():
                delta = task_dict.get("delta", {})
                task_deltas[guid] = delta.get("updates", {})

        process_instance_dict_copy = copy.deepcopy(process_instance_dict)
        bpmn_process_instance = serializer.from_dict(process_instance_dict_copy)

        human_tasks = bpmn_process_instance.get_tasks(manual=True)
        service_tasks = bpmn_process_instance.get_tasks(spec_class=ServiceTaskMixin)
        all_spiff_tasks = human_tasks + service_tasks
        bpmn_unit_test_specification: dict = {"tasks": {}, "expected_output_json": bpmn_process_instance.data}
        for spiff_task in all_spiff_tasks:
            process_id = spiff_task.workflow.spec.name
            bpmn_task_identifier = f"{process_id}:{spiff_task.task_spec.bpmn_id}"
            if bpmn_task_identifier not in bpmn_unit_test_specification["tasks"]:
                bpmn_unit_test_specification["tasks"][bpmn_task_identifier] = {}
            if "data" not in bpmn_unit_test_specification["tasks"][bpmn_task_identifier]:
                bpmn_unit_test_specification["tasks"][bpmn_task_identifier]["data"] = []

            task_data = task_deltas.get(str(spiff_task.id), {})
            bpmn_unit_test_specification["tasks"][bpmn_task_identifier]["data"].append(task_data)

        return {test_case_identifier: bpmn_unit_test_specification}
