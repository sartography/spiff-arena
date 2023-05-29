from dataclasses import dataclass

from SpiffWorkflow.task import Task as SpiffTask  # type: ignore


@dataclass
class ScriptAttributesContext:
    task: SpiffTask | None
    environment_identifier: str
    process_instance_id: int | None
    process_model_identifier: str | None
