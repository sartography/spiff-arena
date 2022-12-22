"""Get_env."""
from collections import OrderedDict
from typing import Any

from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.permission_assignment import PermissionAssignmentModel
from spiffworkflow_backend.models.permission_target import PermissionTargetModel
from spiffworkflow_backend.models.principal import PrincipalModel
from spiffworkflow_backend.models.script_attributes_context import (
    ScriptAttributesContext,
)
from spiffworkflow_backend.scripts.script import Script


# add_permission("read", "test/*", "Editors")


class GetAllPermissions(Script):
    """GetAllPermissions."""

    def get_description(self) -> str:
        """Get_description."""
        return """Get all permissions currently in the system."""

    def run(
        self,
        script_attributes_context: ScriptAttributesContext,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Run."""
        permission_assignments = (
            PermissionAssignmentModel.query.join(
                PrincipalModel,
                PrincipalModel.id == PermissionAssignmentModel.principal_id,
            )
            .join(GroupModel, GroupModel.id == PrincipalModel.group_id)
            .join(
                PermissionTargetModel,
                PermissionTargetModel.id
                == PermissionAssignmentModel.permission_target_id,
            )
            .add_columns(
                PermissionAssignmentModel.permission,
                PermissionTargetModel.uri,
                GroupModel.identifier.label("group_identifier"),
            )
        )

        permissions: OrderedDict[tuple[str, str], list[str]] = OrderedDict()
        for pa in permission_assignments:
            permissions.setdefault((pa.group_identifier, pa.uri), []).append(
                pa.permission
            )

        return [
            {"group_identifier": k[0], "uri": k[1], "permissions": sorted(v)}
            for k, v in permissions.items()
        ]
