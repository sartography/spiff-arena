"""Get_process_info."""
from typing import Any
from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext

from spiffworkflow_backend.scripts.script import Script


class GetProcessInfo(Script):
    """GetUser."""

    def get_description(self) -> str:
        """Get_description."""
        return """Returns a dictionary of information about the currently running process."""

    def run(
        self,
        script_attributes_context: ScriptAttributesContext,
        *_args: Any,
        **kwargs: Any
    ) -> Any:
        """Run."""
        return {
            'process_instance_id': script_attributes_context.process_instance_id,
            'process_model_identifier': script_attributes_context.process_model_identifier,
        }
