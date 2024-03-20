from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Any

from marshmallow import Schema
from marshmallow import post_load


from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import relationship

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db
from sqlalchemy import ForeignKey


@dataclass
class MessageModel(SpiffworkflowBaseDBModel):
    __tablename__ = "message"
    __table_args__ = (UniqueConstraint("identifier", "location", name="_message_identifier_location_unique"),)

    id: int = db.Column(db.Integer, primary_key=True)
    identifier: str = db.Column(db.String(255), index=True, nullable=False)
    location: str = db.Column(db.String(255), nullable=False)
    schema: dict = db.Column(db.JSON, nullable=False)
    updated_at_in_seconds: int = db.Column(db.Integer, nullable=False)
    created_at_in_seconds: int = db.Column(db.Integer, nullable=False)

    correlation_properties = relationship("MessageCorrelationPropertyModel", cascade="delete")
    
@dataclass
class MessageCorrelationPropertyModel(SpiffworkflowBaseDBModel):
    __tablename__ = "message_correlation_property"
    __table_args__ = (UniqueConstraint("message_id", "identifier", "retrieval_expression", name="_message_correlation_property_unique"),)

    id: int = db.Column(db.Integer, primary_key=True)
    message_id: int = db.Column(ForeignKey(MessageModel.id), nullable=False, index=True)  # type: ignore
    identifier: str = db.Column(db.String(255), index=True, nullable=False)
    retrieval_expression: str = db.Column(db.String(255), nullable=False)
    updated_at_in_seconds: int = db.Column(db.Integer, nullable=False)
    created_at_in_seconds: int = db.Column(db.Integer, nullable=False)

    message = relationship("MessageModel", back_populates="correlation_properties")

# @dataclass
# class CorrelationKey:
#     id: str  # A unique string name, lower case, under scores (ie, 'my_key')
#     correlation_properties: list[str]

#     def __eq__(self, other: Any) -> bool:
#         if not isinstance(other, CorrelationKey):
#             return False
#         if other.id == self.id:
#             return True
#         return False

#     def serialized(self) -> dict:
#         return dataclasses.asdict(self)


# class CorrelationKeySchema(Schema):
#     class Meta:
#         model = MessageModel
#         fields = ["id", "correlation_properties"]

#     @post_load
#     def make_key(self, data: dict[str, str | bool | int], **kwargs: dict) -> CorrelationKey:
#         return CorrelationKey(**data)  # type: ignore


# @dataclass
# class RetrievalExpression:
#     message_ref: str
#     formal_expression: str

#     def serialized(self) -> dict:
#         return dataclasses.asdict(self)


# class RetrievalExpressionSchema(Schema):
#     class Meta:
#         model = RetrievalExpression
#         fields = ["message_ref", "formal_expression"]

#     @post_load
#     def make_prop(self, data: dict[str, str | bool | int], **kwargs: dict) -> RetrievalExpression:
#         return RetrievalExpression(**data)  # type: ignore


# @dataclass
# class CorrelationProperty:
#     id: str  # A unique string name, lower case, under scores (ie, 'my_key')
#     retrieval_expressions: list[RetrievalExpression]

#     def serialized(self) -> dict:
#         return dataclasses.asdict(self)


# class CorrelationPropertySchema(Schema):
#     class Meta:
#         model = CorrelationProperty
#         fields = ["id", "retrieval_expressions"]

#     @post_load
#     def make_prop(self, data: dict[str, str | bool | int], **kwargs: dict) -> CorrelationProperty:
#         return CorrelationProperty(**data)  # type: ignore
