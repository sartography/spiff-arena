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
        workflow = script_attributes_context.task.workflow
        task_data_size = ProcessInstanceProcessor.get_task_data_size(workflow)
        task_data_keys_by_task = {
            t.task_spec.name: sorted(t.data.keys())
            for t in ProcessInstanceProcessor.get_tasks_with_data(workflow)
        }
        python_env_size = ProcessInstanceProcessor.get_python_env_size(workflow)
        python_env_keys = workflow.script_engine.environment.user_defined_state().keys()
        return {
            "python_env_size": python_env_size,
            "python_env_keys": sorted(python_env_keys),
            "task_data_size": task_data_size,
            "task_data_keys_by_task": task_data_keys_by_task,
        }
