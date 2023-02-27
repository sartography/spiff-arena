"""Get current user."""
from typing import Any

from flask import current_app

from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.script_attributes_context import (
    ScriptAttributesContext,
)
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.scripts.script import Script


class GetLastUserCompletingTask(Script):
    @staticmethod
    def requires_privileged_permissions() -> bool:
        """We have deemed this function safe to run without elevated permissions."""
        return False

    def get_description(self) -> str:
        return """Return the last user who completed the given task."""

    def run(
        self,
        script_attributes_context: ScriptAttributesContext,
        *_args: Any,
        **kwargs: Any,
    ) -> Any:
        """Run."""
        # dump the user using our json encoder and then load it back up as a dict
        # to remove unwanted field types
        if len(_args) == 2:
            bpmn_process_identifier = _args[0]
            task_name = _args[1]
        else:
            bpmn_process_identifier = kwargs["bpmn_process_identifier"]
            task_name = kwargs["task_bpmn_identifier"]

        human_task = (
            HumanTaskModel.query.filter_by(
                bpmn_process_identifier=bpmn_process_identifier, task_name=task_name
            )
            .order_by(HumanTaskModel.id.desc())  # type: ignore
            .join(UserModel, UserModel.id == HumanTaskModel.completed_by_user_id)
            .first()
        )

        # dump the user using our json encoder and then load it back up as a dict
        # to remove unwanted field types
        user_as_json_string = current_app.json.dumps(human_task.completed_by_user)
        return current_app.json.loads(user_as_json_string)
