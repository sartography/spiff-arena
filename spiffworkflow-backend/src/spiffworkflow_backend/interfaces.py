from typing import TYPE_CHECKING
from typing import NewType
from typing import TypedDict

from spiffworkflow_backend.models.permission_assignment import PermissionAssignmentModel
from spiffworkflow_backend.models.user_group_assignment_waiting import UserGroupAssignmentWaitingModel

if TYPE_CHECKING:
    from spiffworkflow_backend.models.process_group import ProcessGroup


IdToProcessGroupMapping = NewType("IdToProcessGroupMapping", dict[str, "ProcessGroup"])


class ProcessGroupLite(TypedDict):
    id: str
    display_name: str


class ProcessGroupLitesWithCache(TypedDict):
    cache: dict[str, "ProcessGroup"]
    process_groups: list[ProcessGroupLite]


class UserToGroupDict(TypedDict):
    username: str
    group_identifier: str


class AddedPermissionDict(TypedDict):
    group_identifiers: set[str]
    permission_assignments: list[PermissionAssignmentModel]
    user_to_group_identifiers: list[UserToGroupDict]
    waiting_user_group_assignments: list[UserGroupAssignmentWaitingModel]


class DesiredGroupPermissionDict(TypedDict):
    actions: list[str]
    uri: str


class GroupPermissionsDict(TypedDict):
    users: list[str]
    name: str
    permissions: list[DesiredGroupPermissionDict]


class PotentialOwner(TypedDict):
    added_by: str
    user_id: int


class PotentialOwnerIdList(TypedDict):
    potential_owners: list[PotentialOwner]
    lane_assignment_id: int | None
