from dataclasses import dataclass

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.schema import CheckConstraint

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.user import UserModel


class DataValidityError(Exception):
    pass


class MissingPrincipalError(DataValidityError):
    pass


@dataclass
class PrincipalModel(SpiffworkflowBaseDBModel):
    __tablename__ = "principal"
    __table_args__ = (CheckConstraint("NOT(user_id IS NULL AND group_id IS NULL)"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(ForeignKey(UserModel.id), nullable=True, unique=True)  # type: ignore
    group_id = db.Column(ForeignKey(GroupModel.id), nullable=True, unique=True)

    user = relationship("UserModel", viewonly=True)
    group = relationship("GroupModel", viewonly=True)

    permission_assignments = relationship("PermissionAssignmentModel", cascade="delete")  # type: ignore
