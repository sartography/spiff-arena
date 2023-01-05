"""Get_secret."""
from typing import Any

from spiffworkflow_backend.models.script_attributes_context import (
    ScriptAttributesContext,
)
from spiffworkflow_backend.scripts.script import Script
from spiffworkflow_backend.services.secret_service import SecretService


class GetSecret(Script):
    """GetSecret."""

    def get_description(self) -> str:
        """Get_description."""
        return """Returns the value for a previously configured secret."""

    def run(
        self,
        script_attributes_context: ScriptAttributesContext,
        *args: Any,
        **kwargs: Any
    ) -> Any:
        """Run."""
        return SecretService.get_secret(args[0]).value
