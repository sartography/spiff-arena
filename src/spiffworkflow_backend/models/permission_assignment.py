"""PermissionAssignment."""
import enum

from flask_bpmn.models.db import db
from flask_bpmn.models.db import SpiffworkflowBaseDBModel
from sqlalchemy import Enum
from sqlalchemy import ForeignKey

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

    create = 1
    read = 2
    update = 3
    delete = 4
    list = 5
    instantiate = 6  # this is something you do to a process model


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
        ForeignKey(PermissionTargetModel.id), nullable=False
    )
    grant_type = db.Column(Enum(PermitDeny))
    permission = db.Column(Enum(Permission))
