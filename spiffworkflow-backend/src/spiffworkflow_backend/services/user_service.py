"""User_service."""
from typing import Any
from typing import Optional

from flask import current_app
from flask import g
from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.db import db

from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.human_task_user import HumanTaskUserModel
from spiffworkflow_backend.models.principal import PrincipalModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.models.user_group_assignment import UserGroupAssignmentModel
from spiffworkflow_backend.models.user_group_assignment_waiting import (
    UserGroupAssignmentWaitingModel,
)


class UserService:
    """Provides common tools for working with users."""

    @classmethod
    def create_user(
        cls,
        username: str,
        service: str,
        service_id: str,
        email: Optional[str] = "",
        display_name: Optional[str] = "",
    ) -> UserModel:
        """Create_user."""
        user_model: Optional[UserModel] = (
            UserModel.query.filter(UserModel.service == service)
            .filter(UserModel.service_id == service_id)
            .first()
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
            UserService().apply_waiting_group_assignments(user_model)
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
        """Has_user."""
        return "token" in g and bool(g.token) and "user" in g and bool(g.user)

    @staticmethod
    def current_user() -> Any:
        """Current_user."""
        if not UserService.has_user():
            raise ApiError(
                "logged_out", "You are no longer logged in.", status_code=401
            )
        return g.user

    @staticmethod
    def get_principal_by_user_id(user_id: int) -> PrincipalModel:
        """Get_principal_by_user_id."""
        principal = (
            db.session.query(PrincipalModel)
            .filter(PrincipalModel.user_id == user_id)
            .first()
        )
        if isinstance(principal, PrincipalModel):
            return principal
        raise ApiError(
            error_code="no_principal_found",
            message=f"No principal was found for user_id: {user_id}",
        )

    @classmethod
    def create_principal(
        cls, child_id: int, id_column_name: str = "user_id"
    ) -> PrincipalModel:
        """Create_principal."""
        column = PrincipalModel.__table__.columns[id_column_name]
        principal: Optional[PrincipalModel] = PrincipalModel.query.filter(
            column == child_id
        ).first()
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
    def add_user_to_group(cls, user: UserModel, group: GroupModel) -> None:
        """Add_user_to_group."""
        exists = (
            UserGroupAssignmentModel()
            .query.filter_by(user_id=user.id)
            .filter_by(group_id=group.id)
            .count()
        )
        if not exists:
            ugam = UserGroupAssignmentModel(user_id=user.id, group_id=group.id)
            db.session.add(ugam)
            db.session.commit()

    @classmethod
    def add_waiting_group_assignment(cls, username: str, group: GroupModel) -> None:
        """Add_waiting_group_assignment."""
        wugam = (
            UserGroupAssignmentWaitingModel()
            .query.filter_by(username=username)
            .filter_by(group_id=group.id)
            .first()
        )
        if not wugam:
            wugam = UserGroupAssignmentWaitingModel(
                username=username, group_id=group.id
            )
            db.session.add(wugam)
            db.session.commit()
        if wugam.is_match_all():
            for user in UserModel.query.all():
                cls.add_user_to_group(user, group)

    @classmethod
    def apply_waiting_group_assignments(cls, user: UserModel) -> None:
        """Apply_waiting_group_assignments."""
        waiting = (
            UserGroupAssignmentWaitingModel()
            .query.filter(UserGroupAssignmentWaitingModel.username == user.username)
            .all()
        )
        for assignment in waiting:
            cls.add_user_to_group(user, assignment.group)
            db.session.delete(assignment)
        wildcard = (
            UserGroupAssignmentWaitingModel()
            .query.filter(
                UserGroupAssignmentWaitingModel.username
                == UserGroupAssignmentWaitingModel.MATCH_ALL_USERS
            )
            .all()
        )
        for assignment in wildcard:
            cls.add_user_to_group(user, assignment.group)
        db.session.commit()

    @staticmethod
    def get_user_by_service_and_service_id(
        service: str, service_id: str
    ) -> Optional[UserModel]:
        """Get_user_by_service_and_service_id."""
        user: UserModel = (
            UserModel.query.filter(UserModel.service == service)
            .filter(UserModel.service_id == service_id)
            .first()
        )
        if user:
            return user
        return None

    @classmethod
    def add_user_to_human_tasks_if_appropriate(cls, user: UserModel) -> None:
        """Add_user_to_human_tasks_if_appropriate."""
        group_ids = [g.id for g in user.groups]
        human_tasks = HumanTaskModel.query.filter(
            HumanTaskModel.lane_assignment_id.in_(group_ids)  # type: ignore
        ).all()
        for human_task in human_tasks:
            human_task_user = HumanTaskUserModel(
                user_id=user.id, human_task_id=human_task.id
            )
            db.session.add(human_task_user)
            db.session.commit()
