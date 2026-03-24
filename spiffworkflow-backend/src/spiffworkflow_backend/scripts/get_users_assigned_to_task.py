"""Get users assigned to task."""

from typing import Any

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.human_task_user import HumanTaskUserModel
from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.scripts.script import Script


class GetUsersAssignedToTask(Script):
    @staticmethod
    def requires_privileged_permissions() -> bool:
        return False

    def get_description(self) -> str:
        return """Return all users assigned to a task."""

    def run(self, script_attributes_context: ScriptAttributesContext, *_args: Any, **kwargs: Any) -> Any:
        if _args:
            task_guid = _args[0]
        else:
            task_guid = kwargs.get("task_guid")

        if not task_guid:
            raise ValueError("Expected task_guid as first argument or keyword argument")

        rows = (
            db.session.query(UserModel.username)  # type: ignore[no-untyped-call]
            .join(HumanTaskUserModel, HumanTaskUserModel.user_id == UserModel.id)
            .join(HumanTaskModel, HumanTaskModel.id == HumanTaskUserModel.human_task_id)
            .filter(HumanTaskModel.task_guid == task_guid)
            .distinct()
            .all()
        )

        usernames = [r[0] for r in rows]
        return sorted(usernames)
