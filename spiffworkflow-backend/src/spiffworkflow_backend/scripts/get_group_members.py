from typing import Any

from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.group import GroupNotFoundError
from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.script import Script


class GetGroupMembers(Script):
    @staticmethod
    def requires_privileged_permissions() -> bool:
        """We have deemed this function safe to run without elevated permissions."""
        return False

    def get_description(self) -> str:
        return """Return the list of usernames of the users in the given group."""

    def run(
        self,
        script_attributes_context: ScriptAttributesContext,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        group_identifier = args[0]
        group = GroupModel.query.filter_by(identifier=group_identifier).first()
        if group is None:
            raise GroupNotFoundError(f"Script 'get_group_members' could not find group with identifier '{group_identifier}'.")

        usernames = sorted([u.username for u in group.users])
        return usernames
