"""Get_env."""
from typing import Any

from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.group import GroupNotFoundError
from spiffworkflow_backend.models.script_attributes_context import (
    ScriptAttributesContext,
)
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.models.user import UserNotFoundError
from spiffworkflow_backend.scripts.script import Script
from spiffworkflow_backend.services.user_service import UserService


class AddUserToGroup(Script):
    """AddUserToGroup."""

    def get_description(self) -> str:
        """Get_description."""
        return """Add a given user to a given group."""

    def run(
        self,
        script_attributes_context: ScriptAttributesContext,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Run."""
        username = args[0]
        group_identifier = args[1]
        user = UserModel.query.filter_by(username=username).first()
        if user is None:
            raise UserNotFoundError(
                f"Script 'add_user_to_group' could not find a user with username: {username}"
            )

        group = GroupModel.query.filter_by(identifier=group_identifier).first()
        if group is None:
            raise GroupNotFoundError(
                f"Script 'add_user_to_group' could not find group with identifier '{group_identifier}'."
            )

        UserService.add_user_to_group(user, group)
