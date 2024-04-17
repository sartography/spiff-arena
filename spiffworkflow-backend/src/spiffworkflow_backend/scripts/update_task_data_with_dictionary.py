from typing import Any

from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.script import Script


class UpdateTaskDataWithDictionary(Script):
    @staticmethod
    def requires_privileged_permissions() -> bool:
        """We have deemed this function safe to run without elevated permissions."""
        return False

    def get_description(self) -> str:
        return "Updates task data, creating or updating variables named 'key' with 'value' from the given dictionary."

    def run(self, script_attributes_context: ScriptAttributesContext, *args: Any, **kwargs: Any) -> Any:
        updates = args[0]
        spiff_task = script_attributes_context.task

        if spiff_task:
            spiff_task.data.update(updates)
