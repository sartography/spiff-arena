"""Get_env."""
from typing import Any

from spiffworkflow_backend.models.script_attributes_context import (
    ScriptAttributesContext,
)
from spiffworkflow_backend.scripts.script import Script
from spiffworkflow_backend.services.authorization_service import AuthorizationService
from spiffworkflow_backend.services.group_service import GroupService

# add_permission("read", "test/*", "Editors")


class AddPermission(Script):
    """AddUserToGroup."""

    @staticmethod
    def requires_privileged_permissions() -> bool:
        return True

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
        group = GroupService.find_or_create_group(group_identifier)
        target = AuthorizationService.find_or_create_permission_target(uri)
        AuthorizationService.create_permission_for_principal(
            group.principal, target, allowed_permission
        )
