"""Get_env."""
from typing import Any

from spiffworkflow_backend.models.script_attributes_context import (
    ScriptAttributesContext,
)
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.scripts.script import Script
from spiffworkflow_backend.services.group_service import GroupService
from spiffworkflow_backend.services.user_service import UserService


class AddUserToGroup(Script):
    """AddUserToGroup."""

    def get_description(self) -> str:
        """Get_description."""
        return """Add a given user to a given group. Ex. add_user_to_group(group='Education', service_id='1234123')"""

    def run(
        self,
        script_attributes_context: ScriptAttributesContext,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Run."""
        username = args[0]
        group_identifier = args[1]

        group = GroupService.find_or_create_group(group_identifier)
        user = UserModel.query.filter_by(username=username).first()
        if user:
            UserService.add_user_to_group(user, group)
        else:
            UserService.add_waiting_group_assignment(username, group)
