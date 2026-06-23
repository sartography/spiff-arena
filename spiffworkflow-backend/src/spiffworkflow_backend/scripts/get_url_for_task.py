from typing import Any

from flask import current_app

from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.script import Script


class GetUrlForTask(Script):
    @staticmethod
    def requires_privileged_permissions() -> bool:
        return False

    def get_description(self) -> str:
        return """Return the frontend url for a human task."""

    def run(self, script_attributes_context: ScriptAttributesContext, *args: Any, **kwargs: Any) -> Any:
        if args:
            task_guid = args[0]
        else:
            task_guid = kwargs.get("task_guid")

        if not task_guid:
            raise ValueError("Expected task_guid as first argument or keyword argument")

        human_task = HumanTaskModel.query.filter_by(task_guid=task_guid).first()
        if human_task is None:
            raise ValueError(f"Could not find human task with guid '{task_guid}'")

        public = args[1] if len(args) > 1 else kwargs.get("public", False)
        public_segment = "/public" if public is True else ""
        frontend_url = current_app.config["SPIFFWORKFLOW_BACKEND_URL_FOR_FRONTEND"]
        return f"{frontend_url}{public_segment}/tasks/{human_task.process_instance_id}/{human_task.task_guid}"
