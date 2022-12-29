"""User."""
from __future__ import annotations

import jwt
import marshmallow
from flask import current_app
from flask_bpmn.models.db import db
from flask_bpmn.models.db import SpiffworkflowBaseDBModel
from marshmallow import Schema
from sqlalchemy.orm import relationship

from spiffworkflow_backend.models.group import GroupModel


class UserNotFoundError(Exception):
    """UserNotFoundError."""


class UserModel(SpiffworkflowBaseDBModel):
    """UserModel."""

    __tablename__ = "user"
    __table_args__ = (db.UniqueConstraint("service", "service_id", name="service_key"),)
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(
        db.String(255), nullable=False, unique=True
    )  # should always be a unique value
    service = db.Column(
        db.String(255), nullable=False, unique=False
    )  # not 'openid' -- google, aws
    service_id = db.Column(db.String(255), nullable=False, unique=False)
    display_name = db.Column(db.String(255))
    email = db.Column(db.String(255))
    updated_at_in_seconds: int = db.Column(db.Integer)
    created_at_in_seconds: int = db.Column(db.Integer)

    user_group_assignments = relationship("UserGroupAssignmentModel", cascade="delete")  # type: ignore
    groups = relationship(  # type: ignore
        GroupModel,
        viewonly=True,
        secondary="user_group_assignment",
        overlaps="user_group_assignments,users",
    )
    principal = relationship("PrincipalModel", uselist=False)  # type: ignore

    def encode_auth_token(self) -> str:
        """Generate the Auth Token.

        :return: string
        """
        secret_key = current_app.config.get("SECRET_KEY")
        if secret_key is None:
            raise KeyError("we need current_app.config to have a SECRET_KEY")

        # hours = float(app.config['TOKEN_AUTH_TTL_HOURS'])
        payload = {
            # 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=hours, minutes=0, seconds=0),
            # 'iat': datetime.datetime.utcnow(),
            "sub": f"service:{self.service}::service_id:{self.service_id}",
            "token_type": "internal",
        }
        return jwt.encode(
            payload,
            secret_key,
            algorithm="HS256",
        )

    # @classmethod
    # def from_open_id_user_info(cls, user_info: dict) -> Any:
    #     """From_open_id_user_info."""
    #     instance = cls()
    #     instance.service = "keycloak"
    #     instance.service_id = user_info["sub"]
    #     instance.name = user_info["preferred_username"]
    #     instance.username = user_info["sub"]
    #
    #     return instance


class UserModelSchema(Schema):
    """UserModelSchema."""

    class Meta:
        """Meta."""

        model = UserModel
        # load_instance = True
        # include_relationships = False
        # exclude = ("UserGroupAssignment",)

    id = marshmallow.fields.String(required=True)
    username = marshmallow.fields.String(required=True)
