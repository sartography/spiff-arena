import enum
from typing import Any

from sqlalchemy import ForeignKey
from sqlalchemy.orm import validates

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.permission_target import PermissionTargetModel
from spiffworkflow_backend.models.principal import PrincipalModel


class PermitDeny(enum.Enum):
    # permit, aka grant
    permit = "permit"
    deny = "deny"


class Permission(enum.Enum):
    # from original requirements
    # instantiate = 1
    # administer = 2
    # view_instance = 3

    create = "create"
    read = "read"
    update = "update"
    delete = "delete"


class PermissionAssignmentModel(SpiffworkflowBaseDBModel):
    __tablename__ = "permission_assignment"
    __table_args__ = (
        db.UniqueConstraint(
            "principal_id",
            "permission_target_id",
            "permission",
            name="permission_assignment_uniq",
        ),
    )
    id = db.Column(db.Integer, primary_key=True)
    principal_id = db.Column(ForeignKey(PrincipalModel.id), nullable=False, index=True)
    permission_target_id = db.Column(ForeignKey(PermissionTargetModel.id), nullable=False, index=True)  # type: ignore
    permission_target = db.relationship(PermissionTargetModel, backref="permission_assignments")
    grant_type = db.Column(db.String(50), nullable=False)
    permission = db.Column(db.String(50), nullable=False)

    @validates("grant_type")
    def validate_grant_type(self, key: str, value: str) -> Any:
        return self.validate_enum_field(key, value, PermitDeny)

    @validates("permission")
    def validate_permission(self, key: str, value: str) -> Any:
        return self.validate_enum_field(key, value, Permission)

    def __repr__(self) -> str:
        value = (
            f"PermissionAssignmentModel(id={self.id}, target={self.permission_target.uri}, "
            f"permission={self.permission}, grant_type={self.grant_type})"
        )
        return value
