"""Get_env."""
from typing import Any

from spiffworkflow_backend.models.script_attributes_context import (
    ScriptAttributesContext,
)
from spiffworkflow_backend.scripts.script import Script
from spiffworkflow_backend.services.authorization_service import AuthorizationService


class ClearPermissions(Script):
    """Clear all permissions across the system ."""

    def get_description(self) -> str:
        """Get_description."""
        return """Remove all groups and permissions from the database."""

    def run(
        self,
        script_attributes_context: ScriptAttributesContext,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Run."""
        AuthorizationService.delete_all_permissions()
