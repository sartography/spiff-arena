from typing import Any

from SpiffWorkflow.bpmn.serializer import DefaultRegistry  # type: ignore

from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.script import Script

_INTERNAL_KEYS = {"__builtins__", "__annotations__"}


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
        spiff_task = script_attributes_context.task
        if not spiff_task:
            return {}
        data = DefaultRegistry().convert(spiff_task.data)
        return {k: v for k, v in data.items() if k not in _INTERNAL_KEYS}
