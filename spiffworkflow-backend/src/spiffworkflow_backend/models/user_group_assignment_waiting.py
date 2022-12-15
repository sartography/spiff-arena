"""UserGroupAssignment."""
from flask_bpmn.models.db import db
from flask_bpmn.models.db import SpiffworkflowBaseDBModel
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.user import UserModel


class UserGroupAssignmentWaitingModel(SpiffworkflowBaseDBModel):
    """UserGroupAssignmentsWaitingModel - When a user is assinged to a group, but that user has not yet logged into
    the system, this caches that assignment, so it can be applied at the time the user logs in."""

    __tablename__ = "user_group_assignment_waiting"
    __table_args__ = (
        db.UniqueConstraint("username", "group_id", name="user_group_assignment_staged_unique"),
    )

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    group_id = db.Column(ForeignKey(GroupModel.id), nullable=False)

    group = relationship("GroupModel", overlaps="groups,user_group_assignment_waiting,users")  # type: ignore
