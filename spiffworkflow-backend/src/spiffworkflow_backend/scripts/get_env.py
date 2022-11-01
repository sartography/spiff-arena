"""Get_env."""
from typing import Any

from spiffworkflow_backend.models.script_attributes_context import (
    ScriptAttributesContext,
)
from spiffworkflow_backend.scripts.script import Script


class GetEnv(Script):
    """GetEnv."""

    def get_description(self) -> str:
        """Get_description."""
        return """Returns the current environment - ie testing, staging, production."""

    def run(
        self,
        script_attributes_context: ScriptAttributesContext,
        *_args: Any,
        **kwargs: Any
    ) -> Any:
        """Run."""
        return script_attributes_context.environment_identifier
