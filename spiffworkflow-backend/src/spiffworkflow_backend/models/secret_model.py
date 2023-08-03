from dataclasses import dataclass
from typing import Any

from marshmallow import Schema
from sqlalchemy import ForeignKey

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.user import UserModel


@dataclass()
class SecretModel(SpiffworkflowBaseDBModel):
    __tablename__ = "secret"
    id: int = db.Column(db.Integer, primary_key=True)
    key: str = db.Column(db.String(50), unique=True, nullable=False)
    value: str = db.Column(db.Text(), nullable=False)
    user_id: int = db.Column(ForeignKey(UserModel.id), nullable=False, index=True)  # type: ignore
    updated_at_in_seconds: int = db.Column(db.Integer)
    created_at_in_seconds: int = db.Column(db.Integer)

    # value is not included in the serialized output because it is sensitive
    def serialized(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "key": self.key,
            "user_id": self.user_id,
        }


class SecretModelSchema(Schema):
    class Meta:
        model = SecretModel
        fields = ["key", "value", "user_id"]
