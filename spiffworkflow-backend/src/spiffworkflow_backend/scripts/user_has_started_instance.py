from typing import Any

from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.script import Script
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService


class UserHasStartedInstance(Script):
    @staticmethod
    def requires_privileged_permissions() -> bool:
        """We have deemed this function safe to run without elevated permissions."""
        return False

    def get_description(self) -> str:
        return """Returns boolean to indicate if the user has started an instance of the current process model."""

    def run(self, script_attributes_context: ScriptAttributesContext, *_args: Any, **kwargs: Any) -> Any:
        return ProcessInstanceService.user_has_started_instance(script_attributes_context.process_model_identifier)
