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
        from flask import current_app

        group_info = args[0]
        current_app.logger.debug(f"SET PERMISSIONS - START: RefreshPermissions script executing with {len(group_info)} group(s)")

        try:
            for i, group in enumerate(group_info):
                current_app.logger.debug(
                    f"SET PERMISSIONS - Processing group {i + 1}/{len(group_info)}: {group.get('name', 'unknown')}"
                )
                group_name = group.get("name", "unknown")
                num_permissions = len(group.get("permissions", []))
                num_users = len(group.get("users", []))
                current_app.logger.debug(
                    f"SET PERMISSIONS - Group {group_name} has {num_permissions} permission(s) and {num_users} user(s)"
                )

            AuthorizationService.refresh_permissions(group_info, **kwargs)
            current_app.logger.debug("SET PERMISSIONS - COMPLETED: RefreshPermissions script executed successfully")
        except Exception as ex:
            current_app.logger.error(f"SET PERMISSIONS - ERROR: Exception occurred: {str(ex)}")
            raise
