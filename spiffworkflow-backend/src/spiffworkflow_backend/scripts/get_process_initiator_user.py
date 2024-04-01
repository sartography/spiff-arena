"""Get current user."""

from typing import Any

from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.scripts.script import Script


class GetProcessInitiatorUser(Script):
    @staticmethod
    def requires_privileged_permissions() -> bool:
        """We have deemed this function safe to run without elevated permissions."""
        return False

    def get_description(self) -> str:
        return """Return the user that initiated the process instance."""

    def run(
        self,
        script_attributes_context: ScriptAttributesContext,
        *_args: Any,
        **kwargs: Any,
    ) -> Any:
        process_instance = (
            ProcessInstanceModel.query.filter_by(id=script_attributes_context.process_instance_id)
            .join(UserModel, UserModel.id == ProcessInstanceModel.process_initiator_id)
            .first()
        )

        return process_instance.process_initiator.as_dict()
