"""Group_service."""
from typing import Optional

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.user_service import UserService


class GroupService:
    """GroupService."""

    @classmethod
    def find_or_create_group(cls, group_identifier: str) -> GroupModel:
        """Find_or_create_group."""
        group: Optional[GroupModel] = GroupModel.query.filter_by(
            identifier=group_identifier
        ).first()
        if group is None:
            group = GroupModel(identifier=group_identifier)
            db.session.add(group)
            db.session.commit()
            UserService.create_principal(group.id, id_column_name="group_id")
        return group

    @classmethod
    def add_user_to_group_or_add_to_waiting(
        cls, username: str, group_identifier: str
    ) -> None:
        """Add_user_to_group_or_add_to_waiting."""
        group = cls.find_or_create_group(group_identifier)
        user = UserModel.query.filter_by(username=username).first()
        if user:
            UserService.add_user_to_group(user, group)
        else:
            UserService.add_waiting_group_assignment(username, group)
