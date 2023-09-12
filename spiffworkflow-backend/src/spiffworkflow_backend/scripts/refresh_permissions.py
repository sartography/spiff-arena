from typing import Any

from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.script import Script
from spiffworkflow_backend.services.authorization_service import AuthorizationService


class RefreshPermissions(Script):
    def get_description(self) -> str:
        return """Add permissions using a dict.
            If group_permissions_only is True then it will ignore adding and removing users from groups.
            This is useful if the openid server is handling assigning users to groups.

            Example payload:
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
        group_info = args[0]
        AuthorizationService.refresh_permissions(group_info, **kwargs)
