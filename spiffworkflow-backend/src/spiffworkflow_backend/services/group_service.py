from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.user import SPIFF_ANONYMOUS_USER
from spiffworkflow_backend.models.group import SPIFF_NO_AUTH_GROUP, GroupModel
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
    def get_anonymous_user(cls) -> UserModel:
        anonymous_user: UserModel | None = UserModel.query.filter_by(username=SPIFF_ANONYMOUS_USER, service="spiff_anonymous_service", service_id="spiff_anonymous_service_id").first()
        if anonymous_user is None:
            anonymous_user = UserService.create_user(SPIFF_ANONYMOUS_USER, "spiff_anonymous_service", "spiff_anonymous_service_id")
            GroupService.add_user_to_group_or_add_to_waiting(anonymous_user.username, SPIFF_NO_AUTH_GROUP)

        return anonymous_user
