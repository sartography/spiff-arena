from typing import Any

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.human_task_group import HumanTaskGroupModel
from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.script import Script


class GetGroupsAssignedToTask(Script):
    @staticmethod
    def requires_privileged_permissions() -> bool:
        return False

    def get_description(self) -> str:
        return """Return all groups assigned to a human task."""

    def run(self, script_attributes_context: ScriptAttributesContext, *args: Any, **kwargs: Any) -> Any:
        if args:
            task_guid = args[0]
        else:
            task_guid = kwargs.get("task_guid")

        if not task_guid:
            raise ValueError("Expected task_guid as first argument or keyword argument")

        rows = (
            db.session.query(GroupModel)  # type: ignore[no-untyped-call]
            .join(HumanTaskGroupModel, HumanTaskGroupModel.group_id == GroupModel.id)
            .join(HumanTaskModel, HumanTaskModel.id == HumanTaskGroupModel.human_task_id)
            .filter(HumanTaskModel.task_guid == task_guid)
            .distinct()
            .all()
        )

        return [{"id": group.id, "identifier": group.identifier, "name": group.name} for group in rows]
