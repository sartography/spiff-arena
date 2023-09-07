from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.user import UserModel


class UserGroupAssignmentNotFoundError(Exception):
    pass


class UserGroupAssignmentModel(SpiffworkflowBaseDBModel):
    __tablename__ = "user_group_assignment"
    __table_args__ = (db.UniqueConstraint("user_id", "group_id", name="user_group_assignment_unique"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(ForeignKey(UserModel.id), nullable=False, index=True)  # type: ignore
    group_id = db.Column(ForeignKey(GroupModel.id), nullable=False, index=True)

    group = relationship("GroupModel", overlaps="groups,user_group_assignments,users")  # type: ignore
    user = relationship("UserModel", overlaps="groups,user_group_assignments,users")  # type: ignore
