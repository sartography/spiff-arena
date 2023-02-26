"""Get current user."""
from typing import Any
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.models.human_task import HumanTaskModel

from flask import current_app
from flask import g

from spiffworkflow_backend.models.script_attributes_context import (
    ScriptAttributesContext,
)
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
        **kwargs: Any
    ) -> Any:
        """Run."""
        # dump the user using our json encoder and then load it back up as a dict
        # to remove unwanted field types
        if len(_args) == 2:
            process_model_identifier = _args[0]
            task_bpmn_identifier = _args[1]
        else:
            process_model_identifier = kwargs["process_model_identifier"]
            task_bpmn_identifier = kwargs["task_bpmn_identifier"]
        process_model_identifier = _args[0] or kwargs["process_model_identifier"]
        print(f"process_model_identifier: {process_model_identifier}")
        import pdb; pdb.set_trace()
        # human_task = HumanTaskModel.query.filter_by(process_model_identifier=process_model_identifier).order_by(HumanTaskModel.id.desc()).first()
        human_task = HumanTaskModel.query.filter_by(process_model_identifier=process_model_identifier).order_by(HumanTaskModel.id.desc()).join(UserModel, UserModel.id == HumanTaskModel.completed_by_user_id).first()
        return human_task.completed_by_user
        # user_as_json_string = current_app.json.dumps(g.user)
        # return current_app.json.loads(user_as_json_string)
