"""Secret_model."""
from dataclasses import dataclass

from flask_bpmn.models.db import db
from flask_bpmn.models.db import SpiffworkflowBaseDBModel
from marshmallow import Schema
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import RelationshipProperty

from spiffworkflow_backend.models.user import UserModel


@dataclass()
class SecretModel(SpiffworkflowBaseDBModel):
    """SecretModel."""

    __tablename__ = "secret"
    id: int = db.Column(db.Integer, primary_key=True)
    key: str = db.Column(db.String(50), unique=True, nullable=False)
    value: str = db.Column(db.String(255), nullable=False)
    creator_user_id: int = db.Column(ForeignKey(UserModel.id), nullable=False)

    allowed_processes: RelationshipProperty = relationship(
        "SecretAllowedProcessPathModel", cascade="delete"
    )


@dataclass()
class SecretAllowedProcessPathModel(SpiffworkflowBaseDBModel):
    """Allowed processes can be Process Groups or Process Models.

    We store the path in either case.
    """

    __tablename__ = "secret_allowed_process"
    __table_args__ = (
        db.UniqueConstraint(
            "secret_id", "allowed_relative_path", name="unique_secret_path"
        ),
    )

    id: int = db.Column(db.Integer, primary_key=True)
    secret_id: int = db.Column(ForeignKey(SecretModel.id), nullable=False)  # type: ignore
    allowed_relative_path: str = db.Column(db.String(500), nullable=False)


class SecretModelSchema(Schema):
    """SecretModelSchema."""

    class Meta:
        """Meta."""

        model = SecretModel
        fields = ["key", "value", "creator_user_id", "allowed_processes"]


class SecretAllowedProcessSchema(Schema):
    """SecretAllowedProcessSchema."""

    class Meta:
        """Meta."""

        model = SecretAllowedProcessPathModel
        fields = ["secret_id", "allowed_relative_path"]
