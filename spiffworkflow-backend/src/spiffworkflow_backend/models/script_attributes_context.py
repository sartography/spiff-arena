from dataclasses import dataclass
from typing import Optional

from SpiffWorkflow.task import Task as SpiffTask  # type: ignore


@dataclass
class ScriptAttributesContext:
    task: Optional[SpiffTask]
    environment_identifier: str
    process_instance_id: Optional[int]
    process_model_identifier: Optional[str]
