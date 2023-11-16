from typing import Any

from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.script import Script


class GetTaskDataValue(Script):
    @staticmethod
    def requires_privileged_permissions() -> bool:
        """We have deemed this function safe to run without elevated permissions."""
        return False

    def get_description(self) -> str:
        return (
            "Checks to see if given value is in task data and returns its value. "
            "If does not exist or is None, it returns the default value."
        )

    def run(self, script_attributes_context: ScriptAttributesContext, *args: Any, **kwargs: Any) -> Any:
        variable_to_check = args[0]
        default_value = None
        if len(args) > 1:
            default_value = args[1]

        task = script_attributes_context.task
        if task is None:
            return default_value

        task_data = task.data
        if task_data is None:
            return default_value

        if variable_to_check not in task_data.keys():
            return default_value

        value = task_data[variable_to_check]
        if value is None:
            return default_value

        return value
