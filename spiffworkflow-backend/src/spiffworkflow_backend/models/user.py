from __future__ import annotations

import math
import random
import secrets
import string
import time
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
SPIFF_SYSTEM_USER = "spiff_system_user"
SPIFF_GENERATED_JWT_KEY_ID = "spiff_backend"
SPIFF_GENERATED_JWT_ALGORITHM = "HS256"
SPIFF_GENERATED_JWT_AUDIENCE = "spiffworkflow-backend"


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

    @classmethod
    def spiff_generated_jwt_issuer(cls) -> str:
        return str(current_app.config["SPIFFWORKFLOW_BACKEND_URL"])

    def encode_auth_token(self, extra_payload: dict | None = None) -> str:
        """Generate the Auth Token.

        :return: string
        """
        # current_app.secret_key is the same as current_app.config['SECRET_KEY']
        secret_key = str(current_app.secret_key)
        if secret_key is None:
            raise KeyError("we need current_app.config to have a SECRET_KEY")

        one_day_in_seconds = 86400
        # hours = float(app.config['TOKEN_AUTH_TTL_HOURS'])
        base_payload = {
            "email": self.email,
            "preferred_username": self.username,
            "sub": f"service:{self.service}::service_id:{self.service_id}",
            "iss": self.__class__.spiff_generated_jwt_issuer(),
            "iat": math.floor(time.time()),
            "exp": round(time.time()) + one_day_in_seconds,
            "aud": SPIFF_GENERATED_JWT_AUDIENCE,
        }

        payload = base_payload
        if extra_payload is not None:
            payload = {**base_payload, **extra_payload}
        return jwt.encode(
            payload, secret_key, algorithm=SPIFF_GENERATED_JWT_ALGORITHM, headers={"kid": SPIFF_GENERATED_JWT_KEY_ID}
        )

    def as_dict(self) -> dict[str, Any]:
        # dump the user using our json encoder and then load it back up as a dict
        # to remove unwanted field types
        user_as_json_string = current_app.json.dumps(self)
        user_dict: dict[str, Any] = current_app.json.loads(user_as_json_string)
        return user_dict

    @classmethod
    def generate_random_username(cls, prefix: str = "public") -> str:
        adjectives = [
            "fluffy",
            "cuddly",
            "tiny",
            "joyful",
            "sweet",
            "gentle",
            "cheerful",
            "adorable",
            "whiskered",
            "silky",
        ]
        animals = [
            "panda",
            "kitten",
            "puppy",
            "bunny",
            "chick",
            "duckling",
            "chipmunk",
            "hedgehog",
            "lamb",
            "fawn",
            "otter",
            "calf",
            "penguin",
            "koala",
            "giraffe",
            "monkey",
            "fox",
            "raccoon",
            "squirrel",
            "owl",
        ]
        fuzz = "".join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(7))
        # this is not for cryptographic purposes
        adjective = secrets.choice(adjectives)  # noqa: S311
        animal = secrets.choice(animals)  # noqa: S311
        username = f"{prefix}{adjective}{animal}{fuzz}"
        return username
