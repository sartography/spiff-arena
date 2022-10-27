"""Get_env."""
from typing import Any
from typing import Optional

from SpiffWorkflow.task import Task as SpiffTask  # type: ignore
from spiffworkflow_backend.scripts.script import Script


class GetEnv(Script):
    """GetEnv."""

    def get_description(self) -> str:
        """Get_description."""
        return """Returns the current environment - ie testing, staging, production."""

    def run(
        self,
        task: Optional[SpiffTask],
        environment_identifier: str,
        *_args: Any,
        **kwargs: Any
    ) -> Any:
        """Run."""
        return environment_identifier
