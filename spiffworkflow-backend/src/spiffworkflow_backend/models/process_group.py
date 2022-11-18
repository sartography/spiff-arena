"""Process_group."""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from dataclasses import field
from typing import Any

import marshmallow
from marshmallow import post_load
from marshmallow import Schema
from spiffworkflow_backend.models.process_model import ProcessModelInfo


@dataclass(order=True)
class ProcessGroup:
    """ProcessGroup."""

    sort_index: str = field(init=False)

    id: str  # A unique string name, lower case, under scores (ie, 'my_group')
    display_name: str
    description: str | None = None
    display_order: int | None = 0
    admin: bool | None = False
    process_models: list[ProcessModelInfo] = field(
        default_factory=list[ProcessModelInfo]
    )
    process_groups: list[ProcessGroup] = field(default_factory=list["ProcessGroup"])

    def __post_init__(self) -> None:
        """__post_init__."""
        self.sort_index = self.id

    def __eq__(self, other: Any) -> bool:
        """__eq__."""
        if not isinstance(other, ProcessGroup):
            return False
        if other.id == self.id:
            return True
        return False

    @property
    def serialized(self) -> dict:
        """Serialized."""
        original_dict = dataclasses.asdict(self)
        return {x: original_dict[x] for x in original_dict if x not in ["sort_index"]}


class ProcessGroupSchema(Schema):
    """ProcessGroupSchema."""

    class Meta:
        """Meta."""

        model = ProcessGroup
        fields = [
            "id",
            "display_name",
            "display_order",
            "admin",
            "process_models",
            "description",
            "process_groups",
        ]

    process_models = marshmallow.fields.List(
        marshmallow.fields.Nested(
            "ProcessModelInfoSchema", dump_only=True, required=False
        )
    )
    process_groups = marshmallow.fields.List(
        marshmallow.fields.Nested("ProcessGroupSchema", dump_only=True, required=False)
    )

    @post_load
    def make_process_group(
        self, data: dict[str, str | bool | int], **kwargs: dict
    ) -> ProcessGroup:
        """Make_process_group."""
        return ProcessGroup(**data)  # type: ignore
