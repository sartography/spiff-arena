from typing import Any

from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.scripts.script import Script


class GetUserById(Script):
    @staticmethod
    def requires_privileged_permissions() -> bool:
        """We have deemed this function safe to run without elevated permissions."""
        return False

    def get_description(self) -> str:
        return """Gets user by ID."""

    def run(self, script_attributes_context: ScriptAttributesContext, *args: Any, **kwargs: Any) -> Any:
        if "user_id" in kwargs:
            user_id = kwargs["user_id"]
        elif args:
            user_id = args[0]
        else:
            raise ValueError("User ID is required as a positional arg or 'user_id' kwarg")

        user = UserModel.query.filter_by(id=user_id).first()
        if user is not None:
            return user.as_dict()
        return None
