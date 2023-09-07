from typing import Any

from flask import g
from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.models.user_property import UserPropertyModel
from spiffworkflow_backend.scripts.script import Script


class GetUserProperties(Script):
    @staticmethod
    def requires_privileged_permissions() -> bool:
        """We have deemed this function safe to run without elevated permissions."""
        return False

    def get_description(self) -> str:
        return """Gets the user properties for current user."""

    def run(self, script_attributes_context: ScriptAttributesContext, *_args: Any, **kwargs: Any) -> Any:
        user_properties = UserPropertyModel.query.filter_by(user_id=g.user.id).all()
        dict_to_return = {}
        for up in user_properties:
            dict_to_return[up.key] = up.value
        return dict_to_return
