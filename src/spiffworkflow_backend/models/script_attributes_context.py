"""Script_attributes_context."""
from dataclasses import dataclass
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore


@dataclass
class ScriptAttributesContext():
    """ScriptAttributesContext."""
    task: SpiffTask
    environment_identifier: str
    process_instance_id: int
    process_model_identifier: str
