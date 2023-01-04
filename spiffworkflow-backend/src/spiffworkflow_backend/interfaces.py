from typing import NewType, TypedDict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from spiffworkflow_backend.models.process_group import ProcessGroup


IdToProcessGroupMapping = NewType("IdToProcessGroupMapping", dict[str, "ProcessGroup"])


class ProcessGroupLite(TypedDict):

    id: str
    display_name: str


class ProcessGroupLitesWithCache(TypedDict):

    cache: dict[str, "ProcessGroup"]
    process_groups: list[ProcessGroupLite]
