from __future__ import annotations
from hashlib import sha256

import uuid
from dataclasses import dataclass

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db

# this is designed to be used for the "service" column on the user table, which is designed to hold
# information about which authentiation system is used to authenticate this user.
# in this case, we are authenticating based on X-API-KEY which correlates to a known value in the spiff db.
SPIFF_SERVICE_ACCOUNT_AUTH_SERVICE = "spiff_service_account"
SPIFF_SERVICE_ACCOUNT_AUTH_SERVICE_ID_PREFIX = "service_account_"


@dataclass
class ServiceAccountModel(SpiffworkflowBaseDBModel):
    __tablename__ = "service_account"
    __allow_unmapped__ = True
    __table_args__ = (db.UniqueConstraint("name", "created_by_user_id", name="service_account_uniq"),)

    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(255), nullable=False, unique=False, index=True)
    user_id: int = db.Column(ForeignKey("user.id"), nullable=False, index=True)
    created_by_user_id: int = db.Column(ForeignKey("user.id"), nullable=False, index=True)

    api_key_hash: str = db.Column(db.String(255), nullable=False, unique=True, index=True)

    user = relationship("UserModel", uselist=False, cascade="delete", foreign_keys=[user_id])  # type: ignore

    updated_at_in_seconds: int = db.Column(db.Integer)
    created_at_in_seconds: int = db.Column(db.Integer)

    # only to used when the service account first created to tell the user what the key is
    api_key: str | None = None

    @classmethod
    def generate_api_key(cls) -> str:
        return str(uuid.uuid4())

    @classmethod
    def encrypt_api_key(cls, unencrypted_api_key: str) -> str:
        return sha256(unencrypted_api_key.encode("utf8")).hexdigest()
