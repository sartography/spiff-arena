import re
from typing import Any

from flask import current_app
from flask import g
from sqlalchemy import and_
from sqlalchemy import or_

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.interfaces import UserToGroupDict
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.group import SPIFF_GUEST_GROUP
from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.human_task_user import HumanTaskUserAddedBy
from spiffworkflow_backend.models.human_task_user import HumanTaskUserModel
from spiffworkflow_backend.models.principal import MissingPrincipalError
from spiffworkflow_backend.models.principal import PrincipalModel
from spiffworkflow_backend.models.user import SPIFF_GUEST_USER
from spiffworkflow_backend.models.user import SPIFF_SYSTEM_USER
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.models.user_group_assignment import UserGroupAssignmentModel
from spiffworkflow_backend.models.user_group_assignment import UserGroupAssignmentNotFoundError
from spiffworkflow_backend.models.user_group_assignment_waiting import UserGroupAssignmentWaitingModel


class UserService:
    """Provides common tools for working with users."""

    @classmethod
    def create_user(
        cls,
        username: str,
        service: str,
        service_id: str,
        email: str | None = "",
        display_name: str | None = "",
        tenant_specific_field_1: str | None = None,
        tenant_specific_field_2: str | None = None,
        tenant_specific_field_3: str | None = None,
    ) -> UserModel:
        user_model: UserModel | None = (
            UserModel.query.filter(UserModel.service == service).filter(UserModel.service_id == service_id).first()
        )
        if user_model is None:
            if username == "":
                username = service_id

            user_model = UserModel(
                username=username,
                service=service,
                service_id=service_id,
                email=email,
                display_name=display_name,
                tenant_specific_field_1=tenant_specific_field_1,
                tenant_specific_field_2=tenant_specific_field_2,
                tenant_specific_field_3=tenant_specific_field_3,
            )
            db.session.add(user_model)

            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                raise ApiError(
                    error_code="add_user_error",
                    message=f"Could not add user {username}",
                ) from e
            cls.create_principal(user_model.id)
            cls.apply_waiting_group_assignments(user_model)
            return user_model

        else:
            # TODO: username may be ''.
            #  not sure what to send in error message.
            #  Don't really want to send service_id.
            raise (
                ApiError(
                    error_code="user_already_exists",
                    message=f"User already exists: {username}",
                    status_code=409,
                )
            )

    # Returns true if the current user is logged in.
    @staticmethod
    def has_user() -> bool:
        return hasattr(g, "authenticated") and g.authenticated is True and "user" in g and bool(g.user)

    @classmethod
    def current_user(cls) -> Any:
        if not cls.has_user():
            raise ApiError("logged_out", "You are no longer logged in.", status_code=401)
        return g.user

    @staticmethod
    def get_principal_by_user_id(user_id: int) -> PrincipalModel:
        principal = db.session.query(PrincipalModel).filter(PrincipalModel.user_id == user_id).first()
        if isinstance(principal, PrincipalModel):
            return principal
        raise ApiError(
            error_code="no_principal_found",
            message=f"No principal was found for user_id: {user_id}",
        )

    @classmethod
    def create_principal(cls, child_id: int, id_column_name: str = "user_id") -> PrincipalModel:
        column = PrincipalModel.__table__.columns[id_column_name]
        principal: PrincipalModel | None = PrincipalModel.query.filter(column == child_id).first()
        if principal is None:
            principal = PrincipalModel()
            setattr(principal, id_column_name, child_id)
            db.session.add(principal)
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Exception in create_principal: {e}")
                raise ApiError(
                    error_code="add_principal_error",
                    message=f"Could not create principal {child_id}",
                ) from e
        return principal

    @classmethod
    def add_user_to_group(cls, user: UserModel, group: GroupModel) -> GroupModel | None:
        existing_assignment_count = UserGroupAssignmentModel.query.filter_by(user_id=user.id).filter_by(group_id=group.id).count()
        if existing_assignment_count == 0:
            ugam = UserGroupAssignmentModel(user_id=user.id, group_id=group.id)
            db.session.add(ugam)
            db.session.commit()
            return group
        return None

    @classmethod
    def add_waiting_group_assignment(
        cls, username: str, group: GroupModel
    ) -> tuple[UserGroupAssignmentWaitingModel, list[UserToGroupDict]]:
        """Only called from set-permissions."""
        wugam: UserGroupAssignmentWaitingModel | None = (
            UserGroupAssignmentWaitingModel().query.filter_by(username=username).filter_by(group_id=group.id).first()
        )
        if wugam is None:
            wugam = UserGroupAssignmentWaitingModel(username=username, group_id=group.id)
            db.session.add(wugam)
            db.session.commit()

        # backfill existing users
        wildcard_pattern = wugam.pattern_from_wildcard_username()
        user_to_group_identifiers: list[UserToGroupDict] = []
        if wildcard_pattern is not None:
            users = UserModel.query.filter(UserModel.username.regexp_match(wildcard_pattern)).all()  # type: ignore
            for user in users:
                cls.add_user_to_group(user, group)
                user_to_group_identifiers.append({"username": user.username, "group_identifier": group.identifier})

        return (wugam, user_to_group_identifiers)

    @classmethod
    def apply_waiting_group_assignments(cls, user: UserModel) -> None:
        """Only called from create_user which is normally called at sign-in time"""
        waiting = UserGroupAssignmentWaitingModel().query.filter(UserGroupAssignmentWaitingModel.username == user.username).all()
        for assignment in waiting:
            cls.add_user_to_group(user, assignment.group)
            db.session.delete(assignment)
        wildcards = (
            UserGroupAssignmentWaitingModel()
            .query.filter(UserGroupAssignmentWaitingModel.username.regexp_match("^REGEX:"))  # type: ignore
            .all()
        )
        for wildcard in wildcards:
            if re.match(wildcard.pattern_from_wildcard_username(), user.username):
                cls.add_user_to_group(user, wildcard.group)
        db.session.commit()

    @staticmethod
    def get_user_by_service_and_service_id(service: str, service_id: str) -> UserModel | None:
        user: UserModel = UserModel.query.filter(UserModel.service == service).filter(UserModel.service_id == service_id).first()
        if user:
            return user
        return None

    @classmethod
    def update_human_task_assignments_for_user(cls, user: UserModel, new_group_ids: set[int], old_group_ids: set[int]) -> None:
        current_assignments = HumanTaskUserModel.query.filter_by(user_id=user.id).all()
        current_human_task_ids = [ca.human_task_id for ca in current_assignments]
        human_tasks = (
            HumanTaskModel.query.outerjoin(HumanTaskUserModel)
            .filter(
                HumanTaskModel.lane_assignment_id.in_(new_group_ids),  # type: ignore
                HumanTaskModel.completed == False,  # noqa: E712
                or_(
                    and_(
                        HumanTaskUserModel.user_id != user.id,
                        HumanTaskUserModel.added_by == HumanTaskUserAddedBy.lane_assignment.value,
                    ),
                    HumanTaskUserModel.user_id == None,  # noqa: E711
                ),
            )
            .all()
        )

        for human_task in human_tasks:
            if human_task.id not in current_human_task_ids:
                human_task_user = HumanTaskUserModel(
                    user_id=user.id, human_task_id=human_task.id, added_by=HumanTaskUserAddedBy.lane_assignment.value
                )
                db.session.add(human_task_user)
        human_task_assignments_to_delete = (
            HumanTaskUserModel.query.join(HumanTaskModel)
            .filter(
                HumanTaskUserModel.user_id == user.id,
                HumanTaskUserModel.added_by == HumanTaskUserAddedBy.lane_assignment.value,
                HumanTaskModel.lane_assignment_id.in_(old_group_ids),  # type: ignore
                HumanTaskModel.completed == False,  # noqa: E712
            )
            .all()
        )
        for assignment_to_delete in human_task_assignments_to_delete:
            db.session.delete(assignment_to_delete)
        db.session.commit()

    @classmethod
    def get_permission_targets_for_user(cls, user: UserModel, check_groups: bool = True) -> set[tuple[str, str, str]]:
        unique_permission_assignments = set()
        for permission_assignment in user.principal.permission_assignments:
            unique_permission_assignments.add(
                (
                    permission_assignment.permission_target_id,
                    permission_assignment.permission,
                    permission_assignment.grant_type,
                )
            )

        if check_groups:
            for group in user.groups:
                for permission_assignment in group.principal.permission_assignments:
                    unique_permission_assignments.add(
                        (
                            permission_assignment.permission_target_id,
                            permission_assignment.permission,
                            permission_assignment.grant_type,
                        )
                    )
        return unique_permission_assignments

    @classmethod
    def all_principals_for_user(cls, user: UserModel) -> list[PrincipalModel]:
        if user.principal is None:
            raise MissingPrincipalError(f"Missing principal for user with id: {user.id}")

        principals = [user.principal]

        for group in user.groups:
            if group.principal is None:
                raise MissingPrincipalError(f"Missing principal for group with id: {group.id}")
            principals.append(group.principal)

        return principals

    @classmethod
    def find_or_create_group(cls, group_identifier: str, source_is_open_id: bool = False) -> GroupModel:
        group: GroupModel | None = GroupModel.query.filter_by(identifier=group_identifier).first()
        if group is None:
            group = GroupModel(identifier=group_identifier, source_is_open_id=source_is_open_id)
            db.session.add(group)
            db.session.commit()
            cls.create_principal(group.id, id_column_name="group_id")
        elif not group.source_is_open_id and source_is_open_id is True:
            # if a group ever shows up in an open id token we want to flag it to ensure we
            # do not accidentally delete it even if it is mentioned / created in another source
            group.source_is_open_id = True
            db.session.add(group)
            db.session.commit()
        return group

    @classmethod
    def add_user_to_group_or_add_to_waiting(
        cls, username: str | UserModel, group_identifier: str
    ) -> tuple[UserGroupAssignmentWaitingModel | None, list[UserToGroupDict] | None]:
        group = cls.find_or_create_group(group_identifier)
        user = UserModel.query.filter_by(username=username).first()
        if user:
            cls.add_user_to_group(user, group)
        else:
            return cls.add_waiting_group_assignment(username, group)
        return (None, None)

    @classmethod
    def add_user_to_group_by_group_identifier(
        cls, user: UserModel, group_identifier: str, source_is_open_id: bool = False
    ) -> GroupModel | None:
        group = cls.find_or_create_group(group_identifier, source_is_open_id=source_is_open_id)
        return cls.add_user_to_group(user, group)

    @classmethod
    def remove_user_from_group(cls, user: UserModel, group_id: int) -> None:
        user_group_assignment = (
            UserGroupAssignmentModel.query.filter_by(user_id=user.id)
            .join(
                GroupModel,
                and_(GroupModel.id == UserGroupAssignmentModel.group_id, GroupModel.id == group_id),
            )
            .first()
        )
        if user_group_assignment is None:
            raise (UserGroupAssignmentNotFoundError(f"User ({user.username}) is not in group ({group_id})"))
        db.session.delete(user_group_assignment)
        db.session.commit()

    @classmethod
    def find_or_create_guest_user(cls, username: str = SPIFF_GUEST_USER, group_identifier: str = SPIFF_GUEST_GROUP) -> UserModel:
        user: UserModel | None = UserModel.query.filter_by(
            username=username, service="spiff_guest_service", service_id="spiff_guest_service_id"
        ).first()
        if user is None:
            user = cls.create_user(username, "spiff_guest_service", "spiff_guest_service_id")
            cls.add_user_to_group_or_add_to_waiting(user.username, group_identifier)

        return user

    @classmethod
    def find_or_create_system_user(cls, username: str = SPIFF_SYSTEM_USER) -> UserModel:
        user: UserModel | None = UserModel.query.filter_by(
            username=username, service="spiff_system_service", service_id="spiff_system_service_id"
        ).first()
        if user is None:
            user = cls.create_user(username, "spiff_system_service", "spiff_system_service_id")

        return user

    @classmethod
    def create_public_user(cls) -> UserModel:
        username = UserModel.generate_random_username()
        user = UserService.create_user(username, "spiff_public_service", username)
        cls.add_user_to_group_or_add_to_waiting(
            user.username, current_app.config["SPIFFWORKFLOW_BACKEND_DEFAULT_PUBLIC_USER_GROUP"]
        )
        return user
