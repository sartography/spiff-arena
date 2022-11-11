"""Group_service."""
from typing import Optional

from flask_bpmn.models.db import db

from spiffworkflow_backend.models.group import GroupModel
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
