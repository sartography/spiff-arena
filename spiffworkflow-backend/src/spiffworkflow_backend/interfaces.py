"""Interfaces."""
from typing import NewType
from typing import TYPE_CHECKING
from typing import TypedDict

if TYPE_CHECKING:
    from spiffworkflow_backend.models.process_group import ProcessGroup


IdToProcessGroupMapping = NewType("IdToProcessGroupMapping", dict[str, "ProcessGroup"])


class ProcessGroupLite(TypedDict):
    """ProcessGroupLite."""

    id: str
    display_name: str


class ProcessGroupLitesWithCache(TypedDict):
    """ProcessGroupLitesWithCache."""

    cache: dict[str, "ProcessGroup"]
    process_groups: list[ProcessGroupLite]
