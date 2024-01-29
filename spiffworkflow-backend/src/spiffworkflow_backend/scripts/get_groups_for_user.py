from typing import Any

from flask import current_app
from flask import g
from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.script import Script


class GetGroupsForUser(Script):
    @staticmethod
    def requires_privileged_permissions() -> bool:
        """We have deemed this function safe to run without elevated permissions."""
        return False

    def get_description(self) -> str:
        return """Return the list of groups for the current user."""

    def run(
        self,
        script_attributes_context: ScriptAttributesContext,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        groups = g.user.groups
        group_items = [
            group for group in groups if group.identifier != current_app.config["SPIFFWORKFLOW_BACKEND_DEFAULT_USER_GROUP"]
        ]

        group_as_json_string = current_app.json.dumps(group_items)
        return current_app.json.loads(group_as_json_string)
