from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.user_group_assignment import UserGroupAssignmentModel, UserGroupAssignmentNotFoundError
from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.user_service import UserService


class GroupService:
    @classmethod
    def find_or_create_group(cls, group_identifier: str) -> GroupModel:
        group: GroupModel | None = GroupModel.query.filter_by(identifier=group_identifier).first()
        if group is None:
            group = GroupModel(identifier=group_identifier)
            db.session.add(group)
            db.session.commit()
            UserService.create_principal(group.id, id_column_name="group_id")
        return group

    @classmethod
    def add_user_to_group_or_add_to_waiting(cls, username: str | UserModel, group_identifier: str) -> None:
        group = cls.find_or_create_group(group_identifier)
        user = UserModel.query.filter_by(username=username).first()
        if user:
            UserService.add_user_to_group(user, group)
        else:
            UserService.add_waiting_group_assignment(username, group)

    @classmethod
    def add_user_to_group(cls, user: UserModel, group_identifier: str) -> None:
        group = cls.find_or_create_group(group_identifier)
        import pdb; pdb.set_trace()
        UserService.add_user_to_group(user, group)

    @classmethod
    def remove_user_from_group(cls, user: UserModel, group_identifier: str) -> None:
        user_group_assignment = UserGroupAssignmentModel.query.filter_by(user_id=user.id).join(GroupModel, GroupModel.identifier == group_identifier).first()
        if user_group_assignment is None:
            raise (
                UserGroupAssignmentNotFoundError(
                    f"User ({user.username}) is not in group ({group_identifier})"
                )
            )

        db.session.delete(user_group_assignment)
        db.session.commit()
