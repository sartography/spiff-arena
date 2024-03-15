from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Any

from marshmallow import Schema
from marshmallow import post_load


@dataclass
class MessageModel:
    id: str  # A unique string name, lower case, under scores (ie, 'my_message')
    location: str
    schema: dict

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, MessageModel):
            return False
        return other.id == self.id and other.location == self.location

    def serialized(self) -> dict:
        return dataclasses.asdict(self)


class MessageSchema(Schema):
    class Meta:
        model = MessageModel
        fields = ["id"]

    @post_load
    def make_message(self, data: dict[str, str | bool | int], **kwargs: dict) -> MessageModel:
        return MessageModel(**data)  # type: ignore


@dataclass
class CorrelationKey:
    id: str  # A unique string name, lower case, under scores (ie, 'my_key')
    correlation_properties: list[str]

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, CorrelationKey):
            return False
        if other.id == self.id:
            return True
        return False

    def serialized(self) -> dict:
        return dataclasses.asdict(self)


class CorrelationKeySchema(Schema):
    class Meta:
        model = MessageModel
        fields = ["id", "correlation_properties"]

    @post_load
    def make_key(self, data: dict[str, str | bool | int], **kwargs: dict) -> CorrelationKey:
        return CorrelationKey(**data)  # type: ignore


@dataclass
class RetrievalExpression:
    message_ref: str
    formal_expression: str

    def serialized(self) -> dict:
        return dataclasses.asdict(self)


class RetrievalExpressionSchema(Schema):
    class Meta:
        model = RetrievalExpression
        fields = ["message_ref", "formal_expression"]

    @post_load
    def make_prop(self, data: dict[str, str | bool | int], **kwargs: dict) -> RetrievalExpression:
        return RetrievalExpression(**data)  # type: ignore


@dataclass
class CorrelationProperty:
    id: str  # A unique string name, lower case, under scores (ie, 'my_key')
    retrieval_expressions: list[RetrievalExpression]

    def serialized(self) -> dict:
        return dataclasses.asdict(self)


class CorrelationPropertySchema(Schema):
    class Meta:
        model = CorrelationProperty
        fields = ["id", "retrieval_expressions"]

    @post_load
    def make_prop(self, data: dict[str, str | bool | int], **kwargs: dict) -> CorrelationProperty:
        return CorrelationProperty(**data)  # type: ignore
