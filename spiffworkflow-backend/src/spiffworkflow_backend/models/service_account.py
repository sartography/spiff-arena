from __future__ import annotations
import uuid
from sqlalchemy import ForeignKey

from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import relationship

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.group import UserModel

@dataclass
class ServiceAccountModel(SpiffworkflowBaseDBModel):
    __tablename__ = "service_account"
    __table_args__ = (db.UniqueConstraint("name", "created_by_user_id", name="service_account_uniq"),)

    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(255), nullable=False, unique=False, index=True)
    created_by_user_id: int = db.Column(ForeignKey(UserModel.id), nullable=False, index=True)  # type: ignore

    api_key: str = db.Column(db.String(36), nullable=False, unique=True, index=True)

    principal = relationship("PrincipalModel", uselist=False, cascade="delete")  # type: ignore

    updated_at_in_seconds: int = db.Column(db.Integer)
    created_at_in_seconds: int = db.Column(db.Integer)

    @classmethod
    def generate_api_key(cls) -> str:
        return str(uuid.uuid4())
