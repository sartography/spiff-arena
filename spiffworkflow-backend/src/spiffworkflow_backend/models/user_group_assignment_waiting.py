from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.group import GroupModel


class UserGroupAssignmentWaitingModel(SpiffworkflowBaseDBModel):
    """When a user is assigned to a group, but that username does not exist.

    We cache it here to be applied in the event the user does log in to the system.
    """

    __tablename__ = "user_group_assignment_waiting"
    __table_args__ = (db.UniqueConstraint("username", "group_id", name="user_group_assignment_staged_unique"),)

    id: int = db.Column(db.Integer, primary_key=True)
    username: str = db.Column(db.String(255), nullable=False)
    group_id: int = db.Column(ForeignKey(GroupModel.id), nullable=False, index=True)

    group = relationship("GroupModel", overlaps="groups,user_group_assignments_waiting,users")  # type: ignore

    def is_wildcard(self) -> bool:
        if self.username.startswith("REGEX:"):
            return True
        return False

    def pattern_from_wildcard_username(self) -> str | None:
        if self.is_wildcard():
            return self.username.removeprefix("REGEX:")
        return None
