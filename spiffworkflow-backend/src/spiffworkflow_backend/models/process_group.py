from __future__ import annotations

import dataclasses
import os
from dataclasses import dataclass
from dataclasses import field
from typing import Any

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
    correlation_properties: list[CorrelationProperty] | None = None

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
        data = dataclasses.asdict(self)
        data.pop("sort_index", None)
        if self.process_models:
            data["process_models"] = [pm.to_dict() for pm in self.process_models]
        if self.process_groups:
            data["process_groups"] = [pg.serialized() for pg in self.process_groups]
        return data

    def to_dict(self) -> dict:
        """Custom serialization to match Marshmallow schema."""
        messages_list = []
        if self.messages:
            for msg_id, msg_schema in self.messages.items():
                messages_list.append({"id": msg_id, "schema": msg_schema})
        return {
            "id": self.id,
            "display_name": self.display_name,
            "description": self.description,
            "process_groups": [pg.to_dict() for pg in self.process_groups] if self.process_groups else [],
            "messages": messages_list,
            "correlation_properties": [cp.to_dict() for cp in self.correlation_properties] if self.correlation_properties else [],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProcessGroup:
        data_copy = data.copy()
        if "messages" in data_copy and data_copy["messages"] is not None:
            messages_val = data_copy["messages"]
            if isinstance(messages_val, list):
                messages_dict = {}
                for m in messages_val:
                    messages_dict[m["id"]] = m["schema"]
                data_copy["messages"] = messages_dict
        if "correlation_properties" in data_copy and data_copy["correlation_properties"] is not None:
            data_copy["correlation_properties"] = [
                CorrelationProperty.from_dict(cp) for cp in data_copy["correlation_properties"]
            ]
        if "process_groups" in data_copy and data_copy["process_groups"] is not None:
            data_copy["process_groups"] = [ProcessGroup.from_dict(pg) for pg in data_copy["process_groups"]]

        known_fields = {f.name for f in dataclasses.fields(cls)}
        filtered_data = {k: v for k, v in data_copy.items() if k in known_fields}

        return cls(**filtered_data)

    # for use with os.path.join, so it can work on windows
    def id_for_file_path(self) -> str:
        return self.id.replace("/", os.sep)

    @classmethod
    def get_valid_properties(cls) -> list[str]:
        dict_keys = cls.__dataclass_fields__.keys()
        return list(dict_keys)


@dataclass
class RetrievalExpression:
    message_ref: str
    formal_expression: str

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RetrievalExpression:
        return cls(**data)


@dataclass
class CorrelationProperty:
    id: str
    retrieval_expression: RetrievalExpression | None = None

    def to_dict(self) -> dict:
        data = dataclasses.asdict(self)
        if self.retrieval_expression:
            data["retrieval_expression"] = self.retrieval_expression.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CorrelationProperty:
        if "retrieval_expression" in data and data["retrieval_expression"] is not None:
            data["retrieval_expression"] = RetrievalExpression.from_dict(data["retrieval_expression"])
        return cls(**data)
