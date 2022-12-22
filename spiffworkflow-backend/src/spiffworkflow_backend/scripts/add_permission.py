"""Get_env."""
from typing import Any

from spiffworkflow_backend.models.script_attributes_context import (
    ScriptAttributesContext,
)
from spiffworkflow_backend.scripts.script import Script
from spiffworkflow_backend.services.authorization_service import AuthorizationService

# add_permission("read", "test/*", "Editors")


class AddPermission(Script):
    """AddUserToGroup."""

    def get_description(self) -> str:
        """Get_description."""
        return """Add a permission to a group. ex: add_permission("read", "test/*", "Editors") """

    def run(
        self,
        script_attributes_context: ScriptAttributesContext,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Run."""
        allowed_permission = args[0]
        uri = args[1]
        group_identifier = args[2]
        AuthorizationService.add_permission_from_uri_or_macro(
            group_identifier=group_identifier, target=uri, permission=allowed_permission
        )
