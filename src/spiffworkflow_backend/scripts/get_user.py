"""Get_env."""
from typing import Any
from typing import Optional

from flask import g
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore
from spiffworkflow_backend.scripts.script import Script


class GetUser(Script):
    """GetUser."""

    def get_description(self) -> str:
        """Get_description."""
        return """Return the current user."""

    def run(
        self,
        task: Optional[SpiffTask],
        environment_identifier: str,
        *_args: Any,
        **kwargs: Any
    ) -> Any:
        """Run."""
        return g.user.username
