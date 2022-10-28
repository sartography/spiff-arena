"""Get_env."""
from typing import Any

from flask import g
from spiffworkflow_backend.models.script_attributes_context import (
    ScriptAttributesContext,
)
from spiffworkflow_backend.scripts.script import Script


class GetUser(Script):
    """GetUser."""

    def get_description(self) -> str:
        """Get_description."""
        return """Return the current user."""

    def run(
        self,
        script_attributes_context: ScriptAttributesContext,
        *_args: Any,
        **kwargs: Any
    ) -> Any:
        """Run."""
        return g.user.username
