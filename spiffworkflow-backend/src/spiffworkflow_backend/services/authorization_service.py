"""Authorization_service."""
import inspect
import re
from dataclasses import dataclass
from hashlib import sha256
from hmac import compare_digest
from hmac import HMAC
from typing import Any
from typing import Optional
from typing import Set
from typing import TypedDict
from typing import Union

import jwt
import yaml
from flask import current_app
from flask import g
from flask import request
from flask import scaffold
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore
from sqlalchemy import or_
from sqlalchemy import text

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.helpers.api_version import V1_API_PATH_PREFIX
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.permission_assignment import PermissionAssignmentModel
from spiffworkflow_backend.models.permission_target import PermissionTargetModel
from spiffworkflow_backend.models.principal import MissingPrincipalError
from spiffworkflow_backend.models.principal import PrincipalModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.models.user import UserNotFoundError
from spiffworkflow_backend.models.user_group_assignment import UserGroupAssignmentModel
from spiffworkflow_backend.routes.openid_blueprint import openid_blueprint
from spiffworkflow_backend.services.group_service import GroupService
from spiffworkflow_backend.services.user_service import UserService


class PermissionsFileNotSetError(Exception):
    """PermissionsFileNotSetError."""


class HumanTaskNotFoundError(Exception):
    """HumanTaskNotFoundError."""


class UserDoesNotHaveAccessToTaskError(Exception):
    """UserDoesNotHaveAccessToTaskError."""


class InvalidPermissionError(Exception):
    """InvalidPermissionError."""


@dataclass
class PermissionToAssign:
    """PermissionToAssign."""

    permission: str
    target_uri: str


# the relevant permissions are the only API methods that are currently available for each path prefix.
# if we add further API methods, we'll need to evaluate whether they should be added here.
PATH_SEGMENTS_FOR_PERMISSION_ALL = [
    {"path": "/logs", "relevant_permissions": ["read"]},
    {
        "path": "/process-instances",
        "relevant_permissions": ["create", "read", "delete"],
    },
    {"path": "/process-instance-suspend", "relevant_permissions": ["create"]},
    {"path": "/process-instance-terminate", "relevant_permissions": ["create"]},
    {"path": "/task-data", "relevant_permissions": ["read", "update"]},
    {"path": "/process-data", "relevant_permissions": ["read"]},
]


class UserToGroupDict(TypedDict):
    username: str
    group_identifier: str


class DesiredPermissionDict(TypedDict):
    """DesiredPermissionDict."""

    group_identifiers: Set[str]
    permission_assignments: list[PermissionAssignmentModel]
    user_to_group_identifiers: list[UserToGroupDict]


class AuthorizationService:
    """Determine whether a user has permission to perform their request."""

    # https://stackoverflow.com/a/71320673/6090676
    @classmethod
    def verify_sha256_token(cls, auth_header: Optional[str]) -> None:
        """Verify_sha256_token."""
        if auth_header is None:
            raise ApiError(
                error_code="unauthorized",
                message="",
                status_code=403,
            )

        received_sign = auth_header.split("sha256=")[-1].strip()
        secret = current_app.config["GITHUB_WEBHOOK_SECRET"].encode()
        expected_sign = HMAC(key=secret, msg=request.data, digestmod=sha256).hexdigest()
        if not compare_digest(received_sign, expected_sign):
            raise ApiError(
                error_code="unauthorized",
                message="",
                status_code=403,
            )

    @classmethod
    def has_permission(
        cls, principals: list[PrincipalModel], permission: str, target_uri: str
    ) -> bool:
        """Has_permission."""
        principal_ids = [p.id for p in principals]
        target_uri_normalized = target_uri.removeprefix(V1_API_PATH_PREFIX)

        permission_assignments = (
            PermissionAssignmentModel.query.filter(
                PermissionAssignmentModel.principal_id.in_(principal_ids)
            )
            .filter_by(permission=permission)
            .join(PermissionTargetModel)
            .filter(
                or_(
                    text(f"'{target_uri_normalized}' LIKE permission_target.uri"),
                    # to check for exact matches as well
                    # see test_user_can_access_base_path_when_given_wildcard_permission unit test
                    text(
                        f"'{target_uri_normalized}' ="
                        " replace(replace(permission_target.uri, '/%', ''), ':%', '')"
                    ),
                )
            )
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
    def delete_all_permissions(cls) -> None:
        """Delete_all_permissions_and_recreate.  EXCEPT For permissions for the current user?"""
        for model in [PermissionAssignmentModel, PermissionTargetModel]:
            db.session.query(model).delete()

        # cascading to principals doesn't seem to work when attempting to delete all so do it like this instead
        for group in GroupModel.query.all():
            db.session.delete(group)
        db.session.commit()

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
    ) -> DesiredPermissionDict:
        """Import_permissions_from_yaml_file."""
        if current_app.config["SPIFFWORKFLOW_BACKEND_PERMISSIONS_FILE_NAME"] is None:
            raise (
                PermissionsFileNotSetError(
                    "SPIFFWORKFLOW_BACKEND_PERMISSIONS_FILE_NAME needs to be set in"
                    " order to import permissions"
                )
            )

        permission_configs = None
        with open(current_app.config["PERMISSIONS_FILE_FULLPATH"]) as file:
            permission_configs = yaml.safe_load(file)

        default_group = None
        unique_user_group_identifiers: Set[str] = set()
        user_to_group_identifiers: list[UserToGroupDict] = []
        if "default_group" in permission_configs:
            default_group_identifier = permission_configs["default_group"]
            default_group = GroupService.find_or_create_group(default_group_identifier)
            unique_user_group_identifiers.add(default_group_identifier)

        if "groups" in permission_configs:
            for group_identifier, group_config in permission_configs["groups"].items():
                group = GroupService.find_or_create_group(group_identifier)
                unique_user_group_identifiers.add(group_identifier)
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
                    user_to_group_dict: UserToGroupDict = {
                        "username": user.username,
                        "group_identifier": group_identifier,
                    }
                    user_to_group_identifiers.append(user_to_group_dict)
                    cls.associate_user_with_group(user, group)

        permission_assignments = []
        if "permissions" in permission_configs:
            for _permission_identifier, permission_config in permission_configs[
                "permissions"
            ].items():
                uri = permission_config["uri"]
                permission_target = cls.find_or_create_permission_target(uri)

                for allowed_permission in permission_config["allowed_permissions"]:
                    if "groups" in permission_config:
                        for group_identifier in permission_config["groups"]:
                            group = GroupService.find_or_create_group(group_identifier)
                            unique_user_group_identifiers.add(group_identifier)
                            permission_assignments.append(
                                cls.create_permission_for_principal(
                                    group.principal,
                                    permission_target,
                                    allowed_permission,
                                )
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
                                permission_assignments.append(
                                    cls.create_permission_for_principal(
                                        principal, permission_target, allowed_permission
                                    )
                                )

        if default_group is not None:
            for user in UserModel.query.all():
                cls.associate_user_with_group(user, default_group)

        return {
            "group_identifiers": unique_user_group_identifiers,
            "permission_assignments": permission_assignments,
            "user_to_group_identifiers": user_to_group_identifiers,
        }

    @classmethod
    def find_or_create_permission_target(cls, uri: str) -> PermissionTargetModel:
        """Find_or_create_permission_target."""
        uri_with_percent = re.sub(r"\*", "%", uri)
        target_uri_normalized = uri_with_percent.removeprefix(V1_API_PATH_PREFIX)
        permission_target: Optional[PermissionTargetModel] = (
            PermissionTargetModel.query.filter_by(uri=target_uri_normalized).first()
        )
        if permission_target is None:
            permission_target = PermissionTargetModel(uri=target_uri_normalized)
            db.session.add(permission_target)
            db.session.commit()
        return permission_target

    @classmethod
    def create_permission_for_principal(
        cls,
        principal: PrincipalModel,
        permission_target: PermissionTargetModel,
        permission: str,
    ) -> PermissionAssignmentModel:
        """Create_permission_for_principal."""
        permission_assignment: Optional[PermissionAssignmentModel] = (
            PermissionAssignmentModel.query.filter_by(
                principal_id=principal.id,
                permission_target_id=permission_target.id,
                permission=permission,
            ).first()
        )
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
        authentication_exclusion_list = [
            "status",
            "authentication_callback",
            "github_webhook_receive",
        ]
        if request.method == "OPTIONS":
            return True

        # if the endpoint does not exist then let the system 404
        #
        # for some reason this runs before connexion checks if the
        # endpoint exists.
        if not request.endpoint:
            return True

        api_view_function = current_app.view_functions[request.endpoint]
        module = inspect.getmodule(api_view_function)
        if (
            api_view_function
            and api_view_function.__name__.startswith("login")
            or api_view_function.__name__.startswith("logout")
            or api_view_function.__name__.startswith("console_ui_")
            or api_view_function.__name__ in authentication_exclusion_list
            or api_view_function.__name__ in swagger_functions
            or module == openid_blueprint
            or module == scaffold  # don't check permissions for static assets
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
            message=(
                f"User {g.user.username} is not authorized to perform requested action:"
                f" {permission_string} - {request.path}"
            ),
            status_code=403,
        )

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
                (
                    "The Authentication token you provided is invalid. You need a new"
                    " token. "
                ),
            ) from exception

    @staticmethod
    def assert_user_can_complete_spiff_task(
        process_instance_id: int,
        spiff_task: SpiffTask,
        user: UserModel,
    ) -> bool:
        """Assert_user_can_complete_spiff_task."""
        human_task = HumanTaskModel.query.filter_by(
            task_name=spiff_task.task_spec.name,
            process_instance_id=process_instance_id,
        ).first()
        if human_task is None:
            raise HumanTaskNotFoundError(
                f"Could find an human task with task name '{spiff_task.task_spec.name}'"
                f" for process instance '{process_instance_id}'"
            )

        if user not in human_task.potential_owners:
            raise UserDoesNotHaveAccessToTaskError(
                f"User {user.username} does not have access to update"
                f" task'{spiff_task.task_spec.name}' for process instance"
                f" '{process_instance_id}'"
            )
        return True

    @classmethod
    def create_user_from_sign_in(cls, user_info: dict) -> UserModel:
        """Create_user_from_sign_in."""
        """Name, family_name, given_name, middle_name, nickname, preferred_username,"""
        """Profile, picture, website, gender, birthdate, zoneinfo, locale, and updated_at. """
        """Email."""
        is_new_user = False
        user_model = (
            UserModel.query.filter(UserModel.service == user_info["iss"])
            .filter(UserModel.service_id == user_info["sub"])
            .first()
        )
        email = display_name = username = ""
        if "email" in user_info:
            username = user_info["email"]
            email = user_info["email"]
        else:  # we fall back to the sub, which may be very ugly.
            username = user_info["sub"] + "@" + user_info["iss"]

        if "preferred_username" in user_info:
            display_name = user_info["preferred_username"]
        elif "nickname" in user_info:
            display_name = user_info["nickname"]
        elif "name" in user_info:
            display_name = user_info["name"]

        if user_model is None:
            current_app.logger.debug("create_user in login_return")
            is_new_user = True
            user_model = UserService().create_user(
                username=username,
                service=user_info["iss"],
                service_id=user_info["sub"],
                email=email,
                display_name=display_name,
            )

        else:
            # Update with the latest information
            user_model.username = username
            user_model.email = email
            user_model.display_name = display_name
            user_model.service = user_info["iss"]
            user_model.service_id = user_info["sub"]

        # this may eventually get too slow.
        # when it does, be careful about backgrounding, because
        # the user will immediately need permissions to use the site.
        # we are also a little apprehensive about pre-creating users
        # before the user signs in, because we won't know things like
        # the external service user identifier.
        cls.import_permissions_from_yaml_file()

        if is_new_user:
            UserService.add_user_to_human_tasks_if_appropriate(user_model)

        # this cannot be None so ignore mypy
        return user_model  # type: ignore

    @classmethod
    def get_permissions_to_assign(
        cls,
        permission_set: str,
        process_related_path_segment: str,
        target_uris: list[str],
    ) -> list[PermissionToAssign]:
        """Get_permissions_to_assign."""
        permissions = permission_set.split(",")
        if permission_set == "all":
            permissions = ["create", "read", "update", "delete"]

        permissions_to_assign: list[PermissionToAssign] = []

        # we were thinking that if you can start an instance, you ought to be able to:
        #   1. view your own instances.
        #   2. view the logs for these instances.
        if permission_set == "start":
            target_uri = f"/process-instances/{process_related_path_segment}"
            permissions_to_assign.append(
                PermissionToAssign(permission="create", target_uri=target_uri)
            )
            target_uri = f"/process-instances/for-me/{process_related_path_segment}"
            permissions_to_assign.append(
                PermissionToAssign(permission="read", target_uri=target_uri)
            )
            target_uri = f"/logs/{process_related_path_segment}"
            permissions_to_assign.append(
                PermissionToAssign(permission="read", target_uri=target_uri)
            )

        else:
            if permission_set == "all":
                for path_segment_dict in PATH_SEGMENTS_FOR_PERMISSION_ALL:
                    target_uri = (
                        f"{path_segment_dict['path']}/{process_related_path_segment}"
                    )
                    relevant_permissions = path_segment_dict["relevant_permissions"]
                    for permission in relevant_permissions:
                        permissions_to_assign.append(
                            PermissionToAssign(
                                permission=permission, target_uri=target_uri
                            )
                        )

            for target_uri in target_uris:
                for permission in permissions:
                    permissions_to_assign.append(
                        PermissionToAssign(permission=permission, target_uri=target_uri)
                    )

        return permissions_to_assign

    @classmethod
    def set_basic_permissions(cls) -> list[PermissionToAssign]:
        """Set_basic_permissions."""
        permissions_to_assign: list[PermissionToAssign] = []
        permissions_to_assign.append(
            PermissionToAssign(
                permission="read", target_uri="/process-instances/for-me"
            )
        )
        permissions_to_assign.append(
            PermissionToAssign(permission="read", target_uri="/processes")
        )
        permissions_to_assign.append(
            PermissionToAssign(permission="read", target_uri="/service-tasks")
        )
        permissions_to_assign.append(
            PermissionToAssign(
                permission="read", target_uri="/user-groups/for-current-user"
            )
        )
        permissions_to_assign.append(
            PermissionToAssign(
                permission="read", target_uri="/process-instances/find-by-id/*"
            )
        )

        for permission in ["create", "read", "update", "delete"]:
            permissions_to_assign.append(
                PermissionToAssign(
                    permission=permission, target_uri="/process-instances/reports/*"
                )
            )
            permissions_to_assign.append(
                PermissionToAssign(permission=permission, target_uri="/tasks/*")
            )
        return permissions_to_assign

    @classmethod
    def set_process_group_permissions(
        cls, target: str, permission_set: str
    ) -> list[PermissionToAssign]:
        """Set_process_group_permissions."""
        permissions_to_assign: list[PermissionToAssign] = []
        process_group_identifier = (
            target.removeprefix("PG:").replace("/", ":").removeprefix(":")
        )
        process_related_path_segment = f"{process_group_identifier}:*"
        if process_group_identifier == "ALL":
            process_related_path_segment = "*"
        target_uris = [
            f"/process-groups/{process_related_path_segment}",
            f"/process-models/{process_related_path_segment}",
        ]
        permissions_to_assign = permissions_to_assign + cls.get_permissions_to_assign(
            permission_set, process_related_path_segment, target_uris
        )
        return permissions_to_assign

    @classmethod
    def set_process_model_permissions(
        cls, target: str, permission_set: str
    ) -> list[PermissionToAssign]:
        """Set_process_model_permissions."""
        permissions_to_assign: list[PermissionToAssign] = []
        process_model_identifier = (
            target.removeprefix("PM:").replace("/", ":").removeprefix(":")
        )
        process_related_path_segment = f"{process_model_identifier}/*"

        if process_model_identifier == "ALL":
            process_related_path_segment = "*"

        target_uris = [f"/process-models/{process_related_path_segment}"]
        permissions_to_assign = permissions_to_assign + cls.get_permissions_to_assign(
            permission_set, process_related_path_segment, target_uris
        )
        return permissions_to_assign

    @classmethod
    def explode_permissions(
        cls, permission_set: str, target: str
    ) -> list[PermissionToAssign]:
        """Explodes given permissions to and returns list of PermissionToAssign objects.

        These can be used to then iterate through and inserted into the database.
        Target Macros:
            ALL
                * gives access to ALL api endpoints - useful to give admin-like permissions
            PG:[process_group_identifier]
                * affects given process-group and all sub process-groups and process-models
            PM:[process_model_identifier]
                * affects given process-model
            BASIC
                * Basic access to complete tasks and use the site

        Permission Macros:
            all
                * create, read, update, delete
            start
                * create process-instances (aka instantiate or start a process-model)
                * only works with PG and PM target macros
        """
        permissions_to_assign: list[PermissionToAssign] = []
        permissions = permission_set.split(",")
        if permission_set == "all":
            permissions = ["create", "read", "update", "delete"]

        if target.startswith("PG:"):
            permissions_to_assign += cls.set_process_group_permissions(
                target, permission_set
            )
        elif target.startswith("PM:"):
            permissions_to_assign += cls.set_process_model_permissions(
                target, permission_set
            )
        elif permission_set == "start":
            raise InvalidPermissionError(
                "Permission 'start' is only available for macros PM and PG."
            )

        elif target.startswith("BASIC"):
            permissions_to_assign += cls.set_basic_permissions()
        elif target == "ALL":
            for permission in permissions:
                permissions_to_assign.append(
                    PermissionToAssign(permission=permission, target_uri="/*")
                )
        elif target.startswith("/"):
            for permission in permissions:
                permissions_to_assign.append(
                    PermissionToAssign(permission=permission, target_uri=target)
                )
        else:
            raise InvalidPermissionError(
                f"Target uri '{target}' with permission set '{permission_set}' is"
                " invalid. The target uri must either be a macro of PG, PM, BASIC, or"
                " ALL or an api uri."
            )

        return permissions_to_assign

    @classmethod
    def add_permission_from_uri_or_macro(
        cls, group_identifier: str, permission: str, target: str
    ) -> list[PermissionAssignmentModel]:
        """Add_permission_from_uri_or_macro."""
        group = GroupService.find_or_create_group(group_identifier)
        permissions_to_assign = cls.explode_permissions(permission, target)
        permission_assignments = []
        for permission_to_assign in permissions_to_assign:
            permission_target = cls.find_or_create_permission_target(
                permission_to_assign.target_uri
            )
            permission_assignments.append(
                cls.create_permission_for_principal(
                    group.principal, permission_target, permission_to_assign.permission
                )
            )
        return permission_assignments

    @classmethod
    def refresh_permissions(cls, group_info: list[dict[str, Any]]) -> None:
        """Adds new permission assignments and deletes old ones."""
        initial_permission_assignments = PermissionAssignmentModel.query.all()
        initial_user_to_group_assignments = UserGroupAssignmentModel.query.all()
        result = cls.import_permissions_from_yaml_file()
        desired_permission_assignments = result["permission_assignments"]
        desired_group_identifiers = result["group_identifiers"]
        desired_user_to_group_identifiers = result["user_to_group_identifiers"]

        for group in group_info:
            group_identifier = group["name"]
            for username in group["users"]:
                user_to_group_dict: UserToGroupDict = {
                    "username": username,
                    "group_identifier": group_identifier,
                }
                desired_user_to_group_identifiers.append(user_to_group_dict)
                GroupService.add_user_to_group_or_add_to_waiting(
                    username, group_identifier
                )
                desired_group_identifiers.add(group_identifier)
            for permission in group["permissions"]:
                for crud_op in permission["actions"]:
                    desired_permission_assignments.extend(
                        cls.add_permission_from_uri_or_macro(
                            group_identifier=group_identifier,
                            target=permission["uri"],
                            permission=crud_op,
                        )
                    )
                    desired_group_identifiers.add(group_identifier)

        for ipa in initial_permission_assignments:
            if ipa not in desired_permission_assignments:
                db.session.delete(ipa)

        for iutga in initial_user_to_group_assignments:
            current_user_dict: UserToGroupDict = {
                "username": iutga.user.username,
                "group_identifier": iutga.group.identifier,
            }
            if current_user_dict not in desired_user_to_group_identifiers:
                db.session.delete(iutga)

        groups_to_delete = GroupModel.query.filter(
            GroupModel.identifier.not_in(desired_group_identifiers)
        ).all()
        for gtd in groups_to_delete:
            db.session.delete(gtd)
        db.session.commit()


class KeycloakAuthorization:
    """Interface with Keycloak server."""


# class KeycloakClient:
