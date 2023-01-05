"""PermissionAssignment."""
import enum
from typing import Any

from flask_bpmn.models.db import db
from flask_bpmn.models.db import SpiffworkflowBaseDBModel
from sqlalchemy import ForeignKey
from sqlalchemy.orm import validates

from spiffworkflow_backend.models.permission_target import PermissionTargetModel
from spiffworkflow_backend.models.principal import PrincipalModel


class PermitDeny(enum.Enum):
    """PermitDeny."""

    # permit, aka grant
    permit = "permit"
    deny = "deny"


class Permission(enum.Enum):
    """Permission."""

    # from original requirements
    # instantiate = 1
    # administer = 2
    # view_instance = 3

    create = "create"
    read = "read"
    update = "update"
    delete = "delete"


class PermissionAssignmentModel(SpiffworkflowBaseDBModel):
    """PermissionAssignmentModel."""

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
    principal_id = db.Column(ForeignKey(PrincipalModel.id), nullable=False)
    permission_target_id = db.Column(
        ForeignKey(PermissionTargetModel.id), nullable=False  # type: ignore
    )
    grant_type = db.Column(db.String(50), nullable=False)
    permission = db.Column(db.String(50), nullable=False)

    @validates("grant_type")
    def validate_grant_type(self, key: str, value: str) -> Any:
        """Validate_grant_type."""
        return self.validate_enum_field(key, value, PermitDeny)

    @validates("permission")
    def validate_permission(self, key: str, value: str) -> Any:
        """Validate_permission."""
        return self.validate_enum_field(key, value, Permission)
