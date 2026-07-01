from SpiffWorkflow.bpmn.workflow import BpmnWorkflow  # type: ignore

from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.services.process_instance_persistence_service import ProcessInstancePersistenceService
from spiffworkflow_backend.services.process_instance_runtime import ProcessInstanceRuntime


class ProcessInstanceProcessor(ProcessInstanceRuntime):
    """Compatibility alias for historical data migrations."""

    @classmethod
    def persist_bpmn_process_dict(
        cls,
        bpmn_process_dict: dict,
        bpmn_definition_to_task_definitions_mappings: dict,
        process_instance_model: ProcessInstanceModel,
        store_process_instance_events: bool = True,
        bpmn_process_instance: BpmnWorkflow | None = None,
    ) -> None:
        ProcessInstancePersistenceService.persist_bpmn_process_dict(
            bpmn_process_dict,
            bpmn_definition_to_task_definitions_mappings,
            process_instance_model,
            store_process_instance_events,
            bpmn_process_instance,
        )
