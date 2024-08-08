from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from sqlalchemy.orm import relationship
from sqlalchemy.sql import false

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db

if TYPE_CHECKING:
    # noqa: F401
    from spiffworkflow_backend.models.user import UserModel  # noqa: F401
    from spiffworkflow_backend.models.user_group_assignment import UserGroupAssignmentModel  # noqa: F401


SPIFF_NO_AUTH_GROUP = "spiff_no_auth_group"
SPIFF_GUEST_GROUP = "spiff_guest_group"


class GroupNotFoundError(Exception):
    pass


@dataclass
class GroupModel(SpiffworkflowBaseDBModel):
    __tablename__ = "group"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(255), index=True)
    identifier: str = db.Column(db.String(255), index=True)
    source_is_open_id: bool = db.Column(db.Boolean, default=False, server_default=false(), nullable=False, index=True)

    user_group_assignments = relationship("UserGroupAssignmentModel", cascade="delete")
    user_group_assignments_waiting = relationship("UserGroupAssignmentWaitingModel", cascade="delete")  # type: ignore
    users = relationship(  # type: ignore
        "UserModel",
        viewonly=True,
        secondary="user_group_assignment",
        overlaps="user_group_assignments,users",
    )
    principal = relationship("PrincipalModel", uselist=False, cascade="all, delete")  # type: ignore
