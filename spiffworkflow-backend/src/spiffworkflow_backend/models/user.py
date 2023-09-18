from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import jwt
from flask import current_app
from sqlalchemy.orm import relationship

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.group import GroupModel

SPIFF_NO_AUTH_USER = "spiff_no_auth_guest_user"
SPIFF_GUEST_USER = "spiff_guest_user"


class UserNotFoundError(Exception):
    pass


@dataclass
class UserModel(SpiffworkflowBaseDBModel):
    __tablename__ = "user"
    __table_args__ = (db.UniqueConstraint("service", "service_id", name="service_key"),)

    id: int = db.Column(db.Integer, primary_key=True)
    username: str = db.Column(db.String(255), nullable=False, unique=True)
    email: str | None = db.Column(db.String(255), index=True)

    service = db.Column(db.String(255), nullable=False, unique=False, index=True)  # not 'openid' -- google, aws
    service_id = db.Column(db.String(255), nullable=False, unique=False, index=True)

    display_name: str | None = db.Column(db.String(255))
    tenant_specific_field_1: str | None = db.Column(db.String(255))
    tenant_specific_field_2: str | None = db.Column(db.String(255))
    tenant_specific_field_3: str | None = db.Column(db.String(255))
    updated_at_in_seconds: int = db.Column(db.Integer)
    created_at_in_seconds: int = db.Column(db.Integer)

    user_group_assignments = relationship("UserGroupAssignmentModel", cascade="delete")  # type: ignore
    groups = relationship(  # type: ignore
        GroupModel,
        viewonly=True,
        secondary="user_group_assignment",
        overlaps="user_group_assignments,users",
    )
    principal = relationship("PrincipalModel", uselist=False, cascade="delete")  # type: ignore

    def encode_auth_token(self, extra_payload: dict | None = None) -> str:
        """Generate the Auth Token.

        :return: string
        """
        secret_key = current_app.config.get("SECRET_KEY")
        if secret_key is None:
            raise KeyError("we need current_app.config to have a SECRET_KEY")

        # hours = float(app.config['TOKEN_AUTH_TTL_HOURS'])
        base_payload = {
            "email": self.email,
            "preferred_username": self.username,
            "sub": f"service:{self.service}::service_id:{self.service_id}",
            "token_type": "internal",
        }

        payload = base_payload
        if extra_payload is not None:
            payload = {**base_payload, **extra_payload}
        return jwt.encode(
            payload,
            secret_key,
            algorithm="HS256",
        )

    def as_dict(self) -> dict[str, Any]:
        # dump the user using our json encoder and then load it back up as a dict
        # to remove unwanted field types
        user_as_json_string = current_app.json.dumps(self)
        user_dict: dict[str, Any] = current_app.json.loads(user_as_json_string)
        return user_dict
