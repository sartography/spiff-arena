"""UserGroupAssignment."""
from flask_bpmn.models.db import db
from flask_bpmn.models.db import SpiffworkflowBaseDBModel
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from spiffworkflow_backend.models.group import GroupModel


class UserGroupAssignmentWaitingModel(SpiffworkflowBaseDBModel):
    """When a user is assigned to a group, but that username does not exist.

    We cache it here to be applied in the event the user does log in to the system.
    """

    MATCH_ALL_USERS = "*"
    __tablename__ = "user_group_assignment_waiting"
    __table_args__ = (
        db.UniqueConstraint(
            "username", "group_id", name="user_group_assignment_staged_unique"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    group_id = db.Column(ForeignKey(GroupModel.id), nullable=False)

    group = relationship("GroupModel", overlaps="groups,user_group_assignments_waiting,users")  # type: ignore

    def is_match_all(self) -> bool:
        """Is_match_all."""
        if self.username == self.MATCH_ALL_USERS:
            return True
        return False
