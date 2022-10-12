"""Principal."""
from dataclasses import dataclass

from flask_bpmn.models.db import db
from flask_bpmn.models.db import SpiffworkflowBaseDBModel
from sqlalchemy import ForeignKey
from sqlalchemy.schema import CheckConstraint

from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.user import UserModel


class DataValidityError(Exception):
    """DataValidityError."""


class MissingPrincipalError(DataValidityError):
    """MissingPrincipalError."""


@dataclass
class PrincipalModel(SpiffworkflowBaseDBModel):
    """PrincipalModel."""

    __tablename__ = "principal"
    __table_args__ = (CheckConstraint("NOT(user_id IS NULL AND group_id IS NULL)"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(ForeignKey(UserModel.id), nullable=True, unique=True)
    group_id = db.Column(ForeignKey(GroupModel.id), nullable=True, unique=True)
