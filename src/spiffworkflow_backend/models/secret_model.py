"""Secret_model."""
from dataclasses import dataclass

from flask_bpmn.models.db import db
from flask_bpmn.models.db import SpiffworkflowBaseDBModel
from marshmallow import Schema
from sqlalchemy import ForeignKey

from spiffworkflow_backend.models.user import UserModel


@dataclass()
class SecretModel(SpiffworkflowBaseDBModel):
    """SecretModel."""

    __tablename__ = "secret"
    id: int = db.Column(db.Integer, primary_key=True)
    key: str = db.Column(db.String(50), unique=True, nullable=False)
    value: str = db.Column(db.Text(), nullable=False)
    creator_user_id: int = db.Column(ForeignKey(UserModel.id), nullable=False)


class SecretModelSchema(Schema):
    """SecretModelSchema."""

    class Meta:
        """Meta."""

        model = SecretModel
        fields = ["key", "value", "creator_user_id"]
