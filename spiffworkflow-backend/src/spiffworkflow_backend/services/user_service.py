"""User_service."""
from typing import Any
from typing import Optional

from flask import current_app
from flask import g
from flask_bpmn.api.api_error import ApiError
from flask_bpmn.models.db import db
from spiffworkflow_backend.models.active_task import ActiveTaskModel
from spiffworkflow_backend.models.active_task_user import ActiveTaskUserModel
from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.principal import PrincipalModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.models.user_group_assignment import UserGroupAssignmentModel


class UserService:
    """Provides common tools for working with users."""

    @classmethod
    def create_user(
        cls,
        service: str,
        service_id: str,
        name: Optional[str] = "",
        username: Optional[str] = "",
        email: Optional[str] = "",
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
                name=name,
                email=email,
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

    @classmethod
    def find_or_create_user(
        cls,
        service: str,
        service_id: str,
        name: Optional[str] = None,
        username: Optional[str] = None,
        email: Optional[str] = None,
    ) -> UserModel:
        """Find_or_create_user."""
        user_model: UserModel
        try:
            user_model = cls.create_user(
                service=service,
                service_id=service_id,
                name=name,
                username=username,
                email=email,
            )
        except ApiError:
            user_model = (
                UserModel.query.filter(UserModel.service == service)
                .filter(UserModel.service_id == service_id)
                .first()
            )
        return user_model

    # Returns true if the current user is logged in.
    @staticmethod
    def has_user() -> bool:
        """Has_user."""
        return "token" in g and bool(g.token) and "user" in g and bool(g.user)

    # Returns true if the given user uid is different from the current user's uid.
    @staticmethod
    def is_different_user(uid: str) -> bool:
        """Is_different_user."""
        return UserService.has_user() and uid is not None and uid is not g.user.uid

    @staticmethod
    def current_user() -> Any:
        """Current_user."""
        if not UserService.has_user():
            raise ApiError(
                "logged_out", "You are no longer logged in.", status_code=401
            )
        return g.user

    @staticmethod
    def in_list(uids: list[str]) -> bool:
        """Returns true if the current user's id is in the given list of ids.

        False if there is no user, or the user is not in the list.
        """
        if (
            UserService.has_user()
        ):  # If someone is logged in, lock tasks that don't belong to them.
            user = UserService.current_user()
            if user.uid in uids:
                return True
        return False

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
        ugam = UserGroupAssignmentModel(user_id=user.id, group_id=group.id)
        db.session.add(ugam)
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
    def add_user_to_active_tasks_if_appropriate(cls, user: UserModel) -> None:
        """Add_user_to_active_tasks_if_appropriate."""
        group_ids = [g.id for g in user.groups]
        active_tasks = ActiveTaskModel.query.filter(
            ActiveTaskModel.lane_assignment_id.in_(group_ids)  # type: ignore
        ).all()
        for active_task in active_tasks:
            active_task_user = ActiveTaskUserModel(
                user_id=user.id, active_task_id=active_task.id
            )
            db.session.add(active_task_user)
            db.session.commit()
