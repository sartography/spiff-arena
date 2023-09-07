from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.group import SPIFF_GUEST_GROUP
from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.user import SPIFF_GUEST_USER
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
    def add_user_to_group_or_add_to_waiting(cls, username: str, group_identifier: str) -> None:
        group = cls.find_or_create_group(group_identifier)
        user = UserModel.query.filter_by(username=username).first()
        if user:
            UserService.add_user_to_group(user, group)
        else:
            UserService.add_waiting_group_assignment(username, group)

    @classmethod
    def find_or_create_guest_user(
        cls, username: str = SPIFF_GUEST_USER, group_identifier: str = SPIFF_GUEST_GROUP
    ) -> UserModel:
        guest_user: UserModel | None = UserModel.query.filter_by(
            username=username, service="spiff_guest_service", service_id="spiff_guest_service_id"
        ).first()
        if guest_user is None:
            guest_user = UserService.create_user(username, "spiff_guest_service", "spiff_guest_service_id")
            GroupService.add_user_to_group_or_add_to_waiting(guest_user.username, group_identifier)

        return guest_user
