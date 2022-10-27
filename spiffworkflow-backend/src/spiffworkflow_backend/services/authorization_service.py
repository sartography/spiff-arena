"""Authorization_service."""
import re
from typing import Optional
from typing import Union

import jwt
import yaml
from flask import current_app
from flask import g
from flask import request
from flask_bpmn.api.api_error import ApiError
from flask_bpmn.models.db import db
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore
from sqlalchemy import text

from spiffworkflow_backend.models.active_task import ActiveTaskModel
from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.permission_assignment import PermissionAssignmentModel
from spiffworkflow_backend.models.permission_target import PermissionTargetModel
from spiffworkflow_backend.models.principal import MissingPrincipalError
from spiffworkflow_backend.models.principal import PrincipalModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.models.user import UserNotFoundError
from spiffworkflow_backend.models.user_group_assignment import UserGroupAssignmentModel
from spiffworkflow_backend.services.process_instance_processor import (
    ProcessInstanceProcessor,
)
from spiffworkflow_backend.services.user_service import UserService


class PermissionsFileNotSetError(Exception):
    """PermissionsFileNotSetError."""


class ActiveTaskNotFoundError(Exception):
    """ActiveTaskNotFoundError."""


class UserDoesNotHaveAccessToTaskError(Exception):
    """UserDoesNotHaveAccessToTaskError."""


class AuthorizationService:
    """Determine whether a user has permission to perform their request."""

    @classmethod
    def has_permission(
        cls, principals: list[PrincipalModel], permission: str, target_uri: str
    ) -> bool:
        """Has_permission."""
        principal_ids = [p.id for p in principals]

        permission_assignments = (
            PermissionAssignmentModel.query.filter(
                PermissionAssignmentModel.principal_id.in_(principal_ids)
            )
            .filter_by(permission=permission)
            .join(PermissionTargetModel)
            .filter(text(f"'{target_uri}' LIKE permission_target.uri"))
            .all()
        )

        for permission_assignment in permission_assignments:
            if permission_assignment.grant_type == "permit":
                return True
            elif permission_assignment.grant_type == "deny":
                return False
            else:
                raise Exception(
                    f"Unknown grant type: {permission_assignment.grant_type}"
                )

        return False

    @classmethod
    def user_has_permission(
        cls, user: UserModel, permission: str, target_uri: str
    ) -> bool:
        """User_has_permission."""
        if user.principal is None:
            raise MissingPrincipalError(
                f"Missing principal for user with id: {user.id}"
            )

        principals = [user.principal]

        for group in user.groups:
            if group.principal is None:
                raise MissingPrincipalError(
                    f"Missing principal for group with id: {group.id}"
                )
            principals.append(group.principal)

        return cls.has_permission(principals, permission, target_uri)

    @classmethod
    def delete_all_permissions_and_recreate(cls) -> None:
        """Delete_all_permissions_and_recreate."""
        for model in [PermissionAssignmentModel, PermissionTargetModel]:
            db.session.query(model).delete()

        # cascading to principals doesn't seem to work when attempting to delete all so do it like this instead
        for group in GroupModel.query.all():
            db.session.delete(group)

        db.session.commit()
        cls.import_permissions_from_yaml_file()

    @classmethod
    def associate_user_with_group(cls, user: UserModel, group: GroupModel) -> None:
        """Associate_user_with_group."""
        user_group_assignemnt = UserGroupAssignmentModel.query.filter_by(
            user_id=user.id, group_id=group.id
        ).first()
        if user_group_assignemnt is None:
            user_group_assignemnt = UserGroupAssignmentModel(
                user_id=user.id, group_id=group.id
            )
            db.session.add(user_group_assignemnt)
            db.session.commit()

    @classmethod
    def import_permissions_from_yaml_file(
        cls, raise_if_missing_user: bool = False
    ) -> None:
        """Import_permissions_from_yaml_file."""
        if current_app.config["SPIFFWORKFLOW_BACKEND_PERMISSIONS_FILE_NAME"] is None:
            raise (
                PermissionsFileNotSetError(
                    "SPIFFWORKFLOW_BACKEND_PERMISSIONS_FILE_NAME needs to be set in order to import permissions"
                )
            )

        permission_configs = None
        with open(current_app.config["PERMISSIONS_FILE_FULLPATH"]) as file:
            permission_configs = yaml.safe_load(file)

        default_group = None
        if "default_group" in permission_configs:
            default_group_identifier = permission_configs["default_group"]
            default_group = GroupModel.query.filter_by(
                identifier=default_group_identifier
            ).first()
            if default_group is None:
                default_group = GroupModel(identifier=default_group_identifier)
                db.session.add(default_group)
                db.session.commit()
                UserService.create_principal(
                    default_group.id, id_column_name="group_id"
                )

        if "groups" in permission_configs:
            for group_identifier, group_config in permission_configs["groups"].items():
                group = GroupModel.query.filter_by(identifier=group_identifier).first()
                if group is None:
                    group = GroupModel(identifier=group_identifier)
                    db.session.add(group)
                    db.session.commit()
                    UserService.create_principal(group.id, id_column_name="group_id")
                for username in group_config["users"]:
                    user = UserModel.query.filter_by(username=username).first()
                    if user is None:
                        if raise_if_missing_user:
                            raise (
                                UserNotFoundError(
                                    f"Could not find a user with name: {username}"
                                )
                            )
                        continue
                    cls.associate_user_with_group(user, group)

        if "permissions" in permission_configs:
            for _permission_identifier, permission_config in permission_configs[
                "permissions"
            ].items():
                uri = permission_config["uri"]
                uri_with_percent = re.sub(r"\*", "%", uri)
                permission_target = PermissionTargetModel.query.filter_by(
                    uri=uri_with_percent
                ).first()
                if permission_target is None:
                    permission_target = PermissionTargetModel(uri=uri_with_percent)
                    db.session.add(permission_target)
                    db.session.commit()

                for allowed_permission in permission_config["allowed_permissions"]:
                    if "groups" in permission_config:
                        for group_identifier in permission_config["groups"]:
                            principal = (
                                PrincipalModel.query.join(GroupModel)
                                .filter(GroupModel.identifier == group_identifier)
                                .first()
                            )
                            cls.create_permission_for_principal(
                                principal, permission_target, allowed_permission
                            )
                    if "users" in permission_config:
                        for username in permission_config["users"]:
                            user = UserModel.query.filter_by(username=username).first()
                            if user is not None:
                                principal = (
                                    PrincipalModel.query.join(UserModel)
                                    .filter(UserModel.username == username)
                                    .first()
                                )
                                cls.create_permission_for_principal(
                                    principal, permission_target, allowed_permission
                                )

        if default_group is not None:
            for user in UserModel.query.all():
                cls.associate_user_with_group(user, default_group)

    @classmethod
    def create_permission_for_principal(
        cls,
        principal: PrincipalModel,
        permission_target: PermissionTargetModel,
        permission: str,
    ) -> PermissionAssignmentModel:
        """Create_permission_for_principal."""
        permission_assignment: Optional[
            PermissionAssignmentModel
        ] = PermissionAssignmentModel.query.filter_by(
            principal_id=principal.id,
            permission_target_id=permission_target.id,
            permission=permission,
        ).first()
        if permission_assignment is None:
            permission_assignment = PermissionAssignmentModel(
                principal_id=principal.id,
                permission_target_id=permission_target.id,
                permission=permission,
                grant_type="permit",
            )
            db.session.add(permission_assignment)
            db.session.commit()
        return permission_assignment

    @classmethod
    def should_disable_auth_for_request(cls) -> bool:
        """Should_disable_auth_for_request."""
        swagger_functions = ["get_json_spec"]
        authentication_exclusion_list = ["status", "authentication_callback"]
        if request.method == "OPTIONS":
            return True

        # if the endpoint does not exist then let the system 404
        #
        # for some reason this runs before connexion checks if the
        # endpoint exists.
        if not request.endpoint:
            return True

        api_view_function = current_app.view_functions[request.endpoint]
        if (
            api_view_function
            and api_view_function.__name__.startswith("login")
            or api_view_function.__name__.startswith("logout")
            or api_view_function.__name__.startswith("console_ui_")
            or api_view_function.__name__ in authentication_exclusion_list
            or api_view_function.__name__ in swagger_functions
        ):
            return True

        return False

    @classmethod
    def get_permission_from_http_method(cls, http_method: str) -> Optional[str]:
        """Get_permission_from_request_method."""
        request_method_mapper = {
            "POST": "create",
            "GET": "read",
            "PUT": "update",
            "DELETE": "delete",
        }
        if http_method in request_method_mapper:
            return request_method_mapper[http_method]

        return None

    # TODO: we can add the before_request to the blueprint
    # directly when we switch over from connexion routes
    # to blueprint routes
    # @process_api_blueprint.before_request

    @classmethod
    def check_for_permission(cls) -> None:
        """Check_for_permission."""
        if cls.should_disable_auth_for_request():
            return None

        authorization_exclusion_list = ["permissions_check"]

        if not hasattr(g, "user"):
            raise ApiError(
                error_code="user_not_logged_in",
                message="User is not logged in. Please log in",
                status_code=401,
            )

        api_view_function = current_app.view_functions[request.endpoint]
        if (
            api_view_function
            and api_view_function.__name__ in authorization_exclusion_list
        ):
            return None

        permission_string = cls.get_permission_from_http_method(request.method)
        if permission_string:
            has_permission = AuthorizationService.user_has_permission(
                user=g.user,
                permission=permission_string,
                target_uri=request.path,
            )
            if has_permission:
                return None

        raise ApiError(
            error_code="unauthorized",
            message=f"User {g.user.username} is not authorized to perform requested action: {permission_string} - {request.path}",
            status_code=403,
        )

    # def refresh_token(self, token: str) -> str:
    #     """Refresh_token."""
    #     # if isinstance(token, str):
    #     #     token = eval(token)
    #     (
    #         open_id_server_url,
    #         open_id_client_id,
    #         open_id_realm_name,
    #         open_id_client_secret_key,
    #     ) = AuthorizationService.get_open_id_args()
    #     headers = {"Content-Type": "application/x-www-form-urlencoded"}
    #     request_url = f"{open_id_server_url}/realms/{open_id_realm_name}/protocol/openid-connect/token"
    #     data = {
    #         "grant_type": "refresh_token",
    #         "client_id": "spiffworkflow-frontend",
    #         "subject_token": token,
    #         "refresh_token": token,
    #     }
    #     refresh_response = requests.post(request_url, headers=headers, data=data)
    #     refresh_token = json.loads(refresh_response.text)
    #     return refresh_token

    # def get_bearer_token(self, basic_token: str) -> dict:
    #     """Get_bearer_token."""
    #     (
    #         open_id_server_url,
    #         open_id_client_id,
    #         open_id_realm_name,
    #         open_id_client_secret_key,
    #     ) = AuthorizationService.get_open_id_args()
    #
    #     backend_basic_auth_string = f"{open_id_client_id}:{open_id_client_secret_key}"
    #     backend_basic_auth_bytes = bytes(backend_basic_auth_string, encoding="ascii")
    #     backend_basic_auth = base64.b64encode(backend_basic_auth_bytes)
    #
    #     headers = {
    #         "Content-Type": "application/x-www-form-urlencoded",
    #         "Authorization": f"Basic {backend_basic_auth.decode('utf-8')}",
    #     }
    #     data = {
    #         "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
    #         "client_id": open_id_client_id,
    #         "subject_token": basic_token,
    #         "audience": open_id_client_id,
    #     }
    #     request_url = f"{open_id_server_url}/realms/{open_id_realm_name}/protocol/openid-connect/token"
    #
    #     backend_response = requests.post(request_url, headers=headers, data=data)
    #     # json_data = json.loads(backend_response.text)
    #     # bearer_token = json_data['access_token']
    #     bearer_token: dict = json.loads(backend_response.text)
    #     return bearer_token

    @staticmethod
    def decode_auth_token(auth_token: str) -> dict[str, Union[str, None]]:
        """Decode the auth token.

        :param auth_token:
        :return: integer|string
        """
        secret_key = current_app.config.get("SECRET_KEY")
        if secret_key is None:
            raise KeyError("we need current_app.config to have a SECRET_KEY")

        try:
            payload = jwt.decode(auth_token, options={"verify_signature": False})
            return payload
        except jwt.ExpiredSignatureError as exception:
            raise ApiError(
                "token_expired",
                "The Authentication token you provided expired and must be renewed.",
            ) from exception
        except jwt.InvalidTokenError as exception:
            raise ApiError(
                "token_invalid",
                "The Authentication token you provided is invalid. You need a new token. ",
            ) from exception

    @staticmethod
    def assert_user_can_complete_spiff_task(
        processor: ProcessInstanceProcessor,
        spiff_task: SpiffTask,
        user: UserModel,
    ) -> bool:
        """Assert_user_can_complete_spiff_task."""
        active_task = ActiveTaskModel.query.filter_by(
            task_name=spiff_task.task_spec.name,
            process_instance_id=processor.process_instance_model.id,
        ).first()
        if active_task is None:
            raise ActiveTaskNotFoundError(
                f"Could find an active task with task name '{spiff_task.task_spec.name}'"
                f" for process instance '{processor.process_instance_model.id}'"
            )

        if user not in active_task.potential_owners:
            raise UserDoesNotHaveAccessToTaskError(
                f"User {user.username} does not have access to update task'{spiff_task.task_spec.name}'"
                f" for process instance '{processor.process_instance_model.id}'"
            )
        return True

    @classmethod
    def create_user_from_sign_in(cls, user_info: dict) -> UserModel:
        """Create_user_from_sign_in."""
        is_new_user = False
        user_model = (
            UserModel.query.filter(UserModel.service == "open_id")
            .filter(UserModel.service_id == user_info["sub"])
            .first()
        )

        if user_model is None:
            current_app.logger.debug("create_user in login_return")
            is_new_user = True
            name = username = email = ""
            if "name" in user_info:
                name = user_info["name"]
            if "username" in user_info:
                username = user_info["username"]
            elif "preferred_username" in user_info:
                username = user_info["preferred_username"]
            if "email" in user_info:
                email = user_info["email"]
            user_model = UserService().create_user(
                service="open_id",
                service_id=user_info["sub"],
                name=name,
                username=username,
                email=email,
            )

        # this may eventually get too slow.
        # when it does, be careful about backgrounding, because
        # the user will immediately need permissions to use the site.
        # we are also a little apprehensive about pre-creating users
        # before the user signs in, because we won't know things like
        # the external service user identifier.
        cls.import_permissions_from_yaml_file()

        if is_new_user:
            UserService.add_user_to_active_tasks_if_appropriate(user_model)

        # this cannot be None so ignore mypy
        return user_model  # type: ignore


class KeycloakAuthorization:
    """Interface with Keycloak server."""


# class KeycloakClient:
