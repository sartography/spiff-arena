"""Get_env."""
from typing import Any
from spiffworkflow_backend.models.group import GroupModel, GroupNotFoundError

from spiffworkflow_backend.models.script_attributes_context import (
    ScriptAttributesContext,
)
from spiffworkflow_backend.scripts.script import Script


class GetGroupMembers(Script):
    """GetGroupMembers."""

    def get_description(self) -> str:
        """Get_description."""
        return """Return the current user."""

    def run(
        self,
        script_attributes_context: ScriptAttributesContext,
        *args: Any,
        **kwargs: Any
    ) -> Any:
        """Run."""
        group_identifier = args[0]
        group = GroupModel.query.filter_by(identifier=group_identifier).first()
        if group is None:
            raise GroupNotFoundError(
                f"Script 'get_group_members' could not find group with identifier '{group_identifier}'.")

        usernames = [u.username for u in group.users]
        return usernames
