from collections.abc import Callable
from types import ModuleType
from typing import Any

from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.script import Script


def str_prefix_pred(prefix: str) -> Callable[[str], bool]:
    def pred(k: str) -> bool:
        return k.startswith(prefix)

    return pred


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
            return {}

        pred = args[0] if args else lambda k: True
        if isinstance(pred, str):
            pred = str_prefix_pred(args[0])
        if not callable(pred):
            raise ValueError("Optional predicate must either be a string or callable.")

        extracted = {}

        for k, v in list(spiff_task.data.items()):
            if k in ["__builtins__", "__annotations__"] or callable(v) or type(v) is ModuleType:
                continue
            if pred(k):
                extracted[k] = spiff_task.data.pop(k)

        return extracted
