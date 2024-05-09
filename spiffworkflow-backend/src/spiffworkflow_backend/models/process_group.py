from __future__ import annotations

import dataclasses
import os
from dataclasses import dataclass
from dataclasses import field
from typing import Any

import marshmallow
from marshmallow import Schema
from marshmallow import post_load

from spiffworkflow_backend.interfaces import ProcessGroupLite
from spiffworkflow_backend.models.process_model import ProcessModelInfo

# we only want to save these items to the json file
PROCESS_GROUP_SUPPORTED_KEYS_FOR_DISK_SERIALIZATION = [
    "display_name",
    "description",
    "data_store_specifications",
    "messages",
    "correlation_keys",
    "correlation_properties",
]


PROCESS_GROUP_KEYS_TO_UPDATE_FROM_API = [
    "display_name",
    "description",
    "messages",
    "data_store_specifications",
    "correlation_keys",
    "correlation_properties",
]


@dataclass(order=True)
class ProcessGroup:
    sort_index: str = field(init=False)

    id: str  # A unique string name, lower case, under scores (ie, 'my_group')
    display_name: str
    description: str | None = None
    process_models: list[ProcessModelInfo] = field(default_factory=list[ProcessModelInfo])
    process_groups: list[ProcessGroup] = field(default_factory=list["ProcessGroup"])
    data_store_specifications: dict[str, Any] = field(default_factory=dict)
    parent_groups: list[ProcessGroupLite] | None = None
    messages: dict[str, Any] | None = None
    correlation_keys: list[dict[str, Any]] | None = None
    correlation_properties: list[dict[str, Any]] | None = None

    # TODO: delete these once they no no longer mentioned in current
    # process_group.json files
    display_order: int | None = 0
    admin: bool | None = False

    def __post_init__(self) -> None:
        self.sort_index = self.display_name

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, ProcessGroup):
            return False
        if other.id == self.id:
            return True
        return False

    def serialized(self) -> dict:
        original_dict = dataclasses.asdict(self)
        return {x: original_dict[x] for x in original_dict if x not in ["sort_index"]}

    # for use with os.path.join, so it can work on windows
    def id_for_file_path(self) -> str:
        return self.id.replace("/", os.sep)

    @classmethod
    def get_valid_properties(cls) -> list[str]:
        dict_keys = cls.__dataclass_fields__.keys()
        return list(dict_keys)


class MessageSchema(Schema):
    class Meta:
        fields = ["id", "schema"]


class RetrievalExpressionSchema(Schema):
    class Meta:
        fields = ["message_ref", "formal_expression"]


class CorrelationPropertySchema(Schema):
    class Meta:
        fields = ["id", "retrieval_expression"]

    retrieval_expression = marshmallow.fields.Nested(RetrievalExpressionSchema, required=False)


class ProcessGroupSchema(Schema):
    class Meta:
        model = ProcessGroup
        fields = [
            "id",
            "display_name",
            "process_models",
            "description",
            "process_groups",
            "messages",
            "correlation_properties",
        ]

    process_models = marshmallow.fields.List(marshmallow.fields.Nested("ProcessModelInfoSchema", dump_only=True, required=False))
    process_groups = marshmallow.fields.List(marshmallow.fields.Nested("ProcessGroupSchema", dump_only=True, required=False))
    messages = marshmallow.fields.List(marshmallow.fields.Nested(MessageSchema, dump_only=True, required=False))
    correlation_properties = marshmallow.fields.List(
        marshmallow.fields.Nested(CorrelationPropertySchema, dump_only=True, required=False)
    )

    @post_load
    def make_process_group(self, data: dict[str, str | bool | int], **kwargs: dict) -> ProcessGroup:
        return ProcessGroup(**data)  # type: ignore
