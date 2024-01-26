from collections import OrderedDict
from typing import Any

from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.permission_assignment import PermissionAssignmentModel
from spiffworkflow_backend.models.permission_target import PermissionTargetModel
from spiffworkflow_backend.models.principal import PrincipalModel
from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.script import Script


class GetAllPermissions(Script):
    def get_description(self) -> str:
        return """Get all permissions currently in the system."""

    def run(
        self,
        script_attributes_context: ScriptAttributesContext,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        permission_assignments = (
            PermissionAssignmentModel.query.join(
                PrincipalModel,
                PrincipalModel.id == PermissionAssignmentModel.principal_id,
            )
            .join(GroupModel, GroupModel.id == PrincipalModel.group_id)
            .join(
                PermissionTargetModel,
                PermissionTargetModel.id == PermissionAssignmentModel.permission_target_id,
            )
            .add_columns(
                PermissionAssignmentModel.permission,
                PermissionTargetModel.uri,
                GroupModel.identifier.label("group_identifier"),  # type: ignore
            )
            .all()
        )

        permissions: OrderedDict[tuple[str, str], list[str]] = OrderedDict()
        for pa in permission_assignments:
            permissions.setdefault((pa.group_identifier, pa.uri), []).append(pa.permission)

        def replace_suffix(string: str, old: str, new: str) -> str:
            if string.endswith(old):
                return string[: -len(old)] + new
            return string

        # sort list of strings based on a specific order
        def sort_by_order(string_list: list, order: list) -> list:
            return sorted(string_list, key=order.index)

        return [
            {
                "group_identifier": k[0],
                "uri": replace_suffix(k[1], "%", "*"),
                "permissions": sort_by_order(v, ["create", "read", "update", "delete"]),
            }
            for k, v in permissions.items()
        ]
