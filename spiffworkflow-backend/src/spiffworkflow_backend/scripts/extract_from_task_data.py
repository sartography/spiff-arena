from typing import Any

from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.script import Script


class ExtractFromTaskData(Script):
    @staticmethod
    def requires_privileged_permissions() -> bool:
        """We have deemed this function safe to run without elevated permissions."""
        return False

    def get_description(self) -> str:
        return "Removes variables from task data based on an optional predicate and returns them as a dictionary."

    def run(self, script_attributes_context: ScriptAttributesContext, *args: Any, **kwargs: Any) -> Any:
        spiff_task = script_attributes_context.task
        if not spiff_task:
            return
        
        pred = args[0] if args else lambda k: True
        if isinstance(pred, str):
            pred = lambda k: k.startswith(args[0])
        if not callable(pred):
            raise ValueError("Optional predicate must either be a string or callable.")

        keys = list(spiff_task.data.keys())
        extracted = {}

        for key in keys:
            if pred(key) and not callable(spiff_task.data[key]):
                extracted[key] = spiff_task.data.pop(key)

        return extracted
