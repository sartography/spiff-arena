from typing import Any

from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.script import Script
from spiffworkflow_backend.services.bpmn_process_service import BpmnProcessService


class GetCurrentTaskInfo(Script):
    @staticmethod
    def requires_privileged_permissions() -> bool:
        """We have deemed this function safe to run without elevated permissions."""
        return False

    def get_description(self) -> str:
        return """Returns the information about the current task."""

    def run(self, script_attributes_context: ScriptAttributesContext, *_args: Any, **kwargs: Any) -> Any:
        task_dict = BpmnProcessService.serializer.to_dict(script_attributes_context.task)
        task_dict.pop("data")
        # Task data can also be serialized as a delta against the parent task.
        # Neither representation belongs in task metadata, especially while
        # script execution has temporarily added builtins to the task data.
        task_dict.pop("delta", None)
        return task_dict
