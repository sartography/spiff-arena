from typing import Any

from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.script import Script
from spiffworkflow_backend.services.bpmn_process_service import BpmnProcessService
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor


class GetCurrentTaskData(Script):
    @staticmethod
    def requires_privileged_permissions() -> bool:
        """We have deemed this function safe to run without elevated permissions."""
        return False

    def get_description(self) -> str:
        return """Returns the data associated with the current task.
        Be sure to delete any variable this gets stored in to avoid duplicating the tasks data.
        """

    def run(self, script_attributes_context: ScriptAttributesContext, *_args: Any, **kwargs: Any) -> Any:
        task_dict = BpmnProcessService._serializer.to_dict(script_attributes_context.task)
        return task_dict["data"]
