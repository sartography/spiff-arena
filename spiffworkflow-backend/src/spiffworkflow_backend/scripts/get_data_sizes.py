"""Get_data_sizes."""
from typing import Any

from spiffworkflow_backend.models.script_attributes_context import (
    ScriptAttributesContext,
)
from spiffworkflow_backend.scripts.script import Script
from spiffworkflow_backend.services.process_instance_processor import (
    ProcessInstanceProcessor,
)

# from spiffworkflow_backend.servces.process_instance_processor import ProcessInstanceProcessor


class GetDataSizes(Script):
    """GetDataSizes."""

    @staticmethod
    def requires_privileged_permissions() -> bool:
        """We have deemed this function safe to run without elevated permissions."""
        return False

    def get_description(self) -> str:
        """Get_description."""
        return """Returns a dictionary of information about the size of task data and
            the python environment for the currently running process."""

    def run(
        self,
        script_attributes_context: ScriptAttributesContext,
        *_args: Any,
        **kwargs: Any
    ) -> Any:
        """Run."""
        task = script_attributes_context.task
        cumulative_task_data_size = ProcessInstanceProcessor.get_task_data_size(
            task.workflow
        )
        python_env_size = ProcessInstanceProcessor.get_python_env_size(task.workflow)
        return {
            "cumulative_task_data_size": cumulative_task_data_size,
            "python_env_size": python_env_size,
        }
