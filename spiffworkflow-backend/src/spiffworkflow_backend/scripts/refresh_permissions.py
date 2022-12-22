"""Get_env."""
from typing import Any

from spiffworkflow_backend.models.script_attributes_context import (
    ScriptAttributesContext,
)
from spiffworkflow_backend.scripts.script import Script
from spiffworkflow_backend.services.authorization_service import AuthorizationService

# add_permission("read", "test/*", "Editors")


class RecreatePermissions(Script):

    def get_description(self) -> str:
        """Get_description."""
        return """Add permissions using a dict.
            group_info: [
                {
                    'name': group_identifier,
                    'users': array_of_users,
                    'permissions': [
                        {
                            'actions': array_of_actions - create, read, etc,
                            'uri': target_uri
                        }
                    ]
                }
            ]
            """

    def run(
        self,
        script_attributes_context: ScriptAttributesContext,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Run."""
        group_info = args[0]
        AuthorizationService.refresh_permissions(group_info)
