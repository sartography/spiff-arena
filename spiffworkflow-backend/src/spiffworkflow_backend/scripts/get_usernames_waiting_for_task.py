from typing import Any

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.human_task_user_waiting import HumanTaskUserWaitingModel
from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.script import Script


class GetUsernamesWaitingForTask(Script):
    @staticmethod
    def requires_privileged_permissions() -> bool:
        return False

    def get_description(self) -> str:
        return """Return usernames waiting to be assigned to a human task."""

    def run(self, script_attributes_context: ScriptAttributesContext, *args: Any, **kwargs: Any) -> Any:
        if args:
            task_guid = args[0]
        else:
            task_guid = kwargs.get("task_guid")

        if not task_guid:
            raise ValueError("Expected task_guid as first argument or keyword argument")

        rows = (
            db.session.query(HumanTaskUserWaitingModel.username)
            .join(HumanTaskModel, HumanTaskModel.id == HumanTaskUserWaitingModel.human_task_id)
            .filter(HumanTaskModel.task_guid == task_guid)
            .distinct()
            .all()
        )

        return sorted([row[0] for row in rows])
