"""UserGroupAssignment."""
from flask_bpmn.models.db import db
from flask_bpmn.models.db import SpiffworkflowBaseDBModel
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.user import UserModel


class UserGroupAssignmentModel(SpiffworkflowBaseDBModel):
    """UserGroupAssignmentModel."""

    __tablename__ = "user_group_assignment"
    __table_args__ = (
        db.UniqueConstraint("user_id", "group_id", name="user_group_assignment_unique"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(ForeignKey(UserModel.id), nullable=False)  # type: ignore
    group_id = db.Column(ForeignKey(GroupModel.id), nullable=False)

    group = relationship("GroupModel", overlaps="groups,user_group_assignments,users")  # type: ignore
    user = relationship("UserModel", overlaps="groups,user_group_assignments,users")  # type: ignore
