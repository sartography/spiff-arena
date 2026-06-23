from typing import Any

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.human_task_group import HumanTaskGroupModel
from spiffworkflow_backend.models.human_task_user import HumanTaskUserModel
from spiffworkflow_backend.models.human_task_user_waiting import HumanTaskUserWaitingModel
from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.scripts.script import Script


class GetTaskPotentialOwners(Script):
    @staticmethod
    def requires_privileged_permissions() -> bool:
        return False

    def get_description(self) -> str:
        return """Return users and groups that can complete a human task."""

    def run(self, script_attributes_context: ScriptAttributesContext, *args: Any, **kwargs: Any) -> Any:
        if args:
            task_guid = args[0]
        else:
            task_guid = kwargs.get("task_guid")

        if not task_guid:
            raise ValueError("Expected task_guid as first argument or keyword argument")

        user_rows = (
            db.session.query(UserModel.username)  # type: ignore[no-untyped-call]
            .join(HumanTaskUserModel, HumanTaskUserModel.user_id == UserModel.id)
            .join(HumanTaskModel, HumanTaskModel.id == HumanTaskUserModel.human_task_id)
            .filter(HumanTaskModel.task_guid == task_guid)
            .distinct()
            .all()
        )

        waiting_rows = (
            db.session.query(HumanTaskUserWaitingModel.username)  # type: ignore[no-untyped-call]
            .join(HumanTaskModel, HumanTaskModel.id == HumanTaskUserWaitingModel.human_task_id)
            .filter(HumanTaskModel.task_guid == task_guid)
            .distinct()
            .all()
        )

        groups = (
            db.session.query(GroupModel)  # type: ignore[no-untyped-call]
            .join(HumanTaskGroupModel, HumanTaskGroupModel.group_id == GroupModel.id)
            .join(HumanTaskModel, HumanTaskModel.id == HumanTaskGroupModel.human_task_id)
            .filter(HumanTaskModel.task_guid == task_guid)
            .distinct()
            .all()
        )

        usernames = sorted({row[0] for row in user_rows} | {row[0] for row in waiting_rows})

        return {
            "users": usernames,
            "groups": sorted([group.identifier for group in groups]),
        }
