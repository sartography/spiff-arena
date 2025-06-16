from typing import Any

from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.scripts.script import Script


class GetUser(Script):
    @staticmethod
    def requires_privileged_permissions() -> bool:
        """We have deemed this function safe to run without elevated permissions."""
        return False

    def get_description(self) -> str:
        return """Gets user by username."""

    def run(self, script_attributes_context: ScriptAttributesContext, *args: Any, **kwargs: Any) -> Any:
        if "username" in kwargs:
            user = UserModel.query.filter_by(username=kwargs["username"]).first()
        else:
            user = UserModel.query.filter_by(username=args[0]).first()
        if user is not None:
            return user.as_dict()
        return None
