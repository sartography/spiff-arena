"""Group."""
from __future__ import annotations

from typing import TYPE_CHECKING

from spiffworkflow_backend.models.db import db, SpiffworkflowBaseDBModel
from sqlalchemy.orm import relationship

if TYPE_CHECKING:
    from spiffworkflow_backend.models.user_group_assignment import (  # noqa: F401
        UserGroupAssignmentModel,
    )  # noqa: F401
    from spiffworkflow_backend.models.user import UserModel  # noqa: F401


class GroupNotFoundError(Exception):
    """GroupNotFoundError."""


class GroupModel(SpiffworkflowBaseDBModel):
    """GroupModel."""

    __tablename__ = "group"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    identifier = db.Column(db.String(255))

    user_group_assignments = relationship("UserGroupAssignmentModel", cascade="delete")
    user_group_assignments_waiting = relationship(  # type: ignore
        "UserGroupAssignmentWaitingModel", cascade="delete"
    )
    users = relationship(  # type: ignore
        "UserModel",
        viewonly=True,
        secondary="user_group_assignment",
        overlaps="user_group_assignments,users",
    )
    principal = relationship("PrincipalModel", uselist=False, cascade="all, delete")  # type: ignore
