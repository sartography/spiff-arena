import inspect
import re
from dataclasses import dataclass
from hashlib import sha256
from hmac import HMAC
from hmac import compare_digest
from typing import TypedDict

import jwt
import yaml
from flask import current_app
from flask import g
from flask import request
from flask import scaffold
from spiffworkflow_backend.helpers.api_version import V1_API_PATH_PREFIX
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.group import SPIFF_GUEST_GROUP
from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.permission_assignment import PermissionAssignmentModel
from spiffworkflow_backend.models.permission_target import PermissionTargetModel
from spiffworkflow_backend.models.principal import MissingPrincipalError
from spiffworkflow_backend.models.principal import PrincipalModel
from spiffworkflow_backend.models.service_account import SPIFF_SERVICE_ACCOUNT_AUTH_SERVICE
from spiffworkflow_backend.models.task import TaskModel  # noqa: F401
from spiffworkflow_backend.models.user import SPIFF_GUEST_USER
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.models.user_group_assignment import UserGroupAssignmentModel
from spiffworkflow_backend.routes.openid_blueprint import openid_blueprint
from spiffworkflow_backend.services.authentication_service import NotAuthorizedError
from spiffworkflow_backend.services.authentication_service import TokenExpiredError
from spiffworkflow_backend.services.authentication_service import TokenInvalidError
from spiffworkflow_backend.services.authentication_service import TokenNotProvidedError
from spiffworkflow_backend.services.authentication_service import UserNotLoggedInError
from spiffworkflow_backend.services.group_service import GroupService
from spiffworkflow_backend.services.user_service import UserService
from sqlalchemy import and_
from sqlalchemy import or_
from sqlalchemy import text


class PermissionsFileNotSetError(Exception):
    pass


class HumanTaskNotFoundError(Exception):
    pass


class HumanTaskAlreadyCompletedError(Exception):
    pass


class UserDoesNotHaveAccessToTaskError(Exception):
    pass


class InvalidPermissionError(Exception):
    pass


@dataclass
class PermissionToAssign:
    permission: str
    target_uri: str


# you can explicitly call out the CRUD actions you want to permit. These include: ["create", "read", "update", "delete"]
# if you hate typing, you can instead specify "all". If you do this, you might think it would grant access to
# ["create", "read", "update", "delete"] for everything. instead, we do this cute thing where we, as the API authors,
# understand that not all verbs are relevant for all API paths. For example, you cannot create logs over the API at this juncture,
# so for /logs, only "read" is relevant. When you ask for /logs, "all", we give you read.
# the relevant permissions are the only API methods that are currently available for each path prefix.
# if we add further API methods, we'll need to evaluate whether they should be added here.
PATH_SEGMENTS_FOR_PERMISSION_ALL = [
    {"path": "/event-error-details", "relevant_permissions": ["read"]},
    {"path": "/logs", "relevant_permissions": ["read"]},
    {"path": "/logs/typeahead-filter-values", "relevant_permissions": ["read"]},
    {
        "path": "/process-instances",
        "relevant_permissions": ["create", "read", "delete"],
    },
    {
        "path": "/process-instances/for-me",
        "relevant_permissions": ["read"],
    },
    {"path": "/process-data", "relevant_permissions": ["read"]},
    {"path": "/process-data-file-download", "relevant_permissions": ["read"]},
    {"path": "/process-instance-suspend", "relevant_permissions": ["create"]},
    {"path": "/process-instance-terminate", "relevant_permissions": ["create"]},
    {"path": "/process-model-natural-language", "relevant_permissions": ["create"]},
    {"path": "/process-model-publish", "relevant_permissions": ["create"]},
    {"path": "/process-model-tests", "relevant_permissions": ["create"]},
    {"path": "/task-assign", "relevant_permissions": ["create"]},
    {"path": "/task-data", "relevant_permissions": ["read", "update"]},
]


class UserToGroupDict(TypedDict):
    username: str
    group_identifier: str


class AddedPermissionDict(TypedDict):
    group_identifiers: set[str]
    permission_assignments: list[PermissionAssignmentModel]
    user_to_group_identifiers: list[UserToGroupDict]


class DesiredGroupPermissionDict(TypedDict):
    actions: list[str]
    uri: str


class GroupPermissionsDict(TypedDict):
    users: list[str]
    name: str
    permissions: list[DesiredGroupPermissionDict]


class AuthorizationService:
    """Determine whether a user has permission to perform their request."""

    # https://stackoverflow.com/a/71320673/6090676
    @classmethod
    def verify_sha256_token(cls, auth_header: str | None) -> None:
        if auth_header is None:
            raise TokenNotProvidedError(
                "unauthorized",
            )

        received_sign = auth_header.split("sha256=")[-1].strip()
        secret = current_app.config["SPIFFWORKFLOW_BACKEND_GITHUB_WEBHOOK_SECRET"].encode()
        expected_sign = HMAC(key=secret, msg=request.data, digestmod=sha256).hexdigest()
        if not compare_digest(received_sign, expected_sign):
            raise TokenInvalidError(
                "unauthorized",
            )

    @classmethod
    def create_guest_token(
        cls,
        username: str,
        group_identifier: str,
        permission_target: str | None = None,
        permission: str = "all",
        auth_token_properties: dict | None = None,
    ) -> None:
        guest_user = GroupService.find_or_create_guest_user(username=username, group_identifier=group_identifier)
        if permission_target is not None:
            cls.add_permission_from_uri_or_macro(group_identifier, permission=permission, target=permission_target)
        g.user = guest_user
        g.token = guest_user.encode_auth_token(auth_token_properties)
        tld = current_app.config["THREAD_LOCAL_DATA"]
        tld.new_access_token = g.token
        tld.new_id_token = g.token

    @classmethod
    def has_permission(cls, principals: list[PrincipalModel], permission: str, target_uri: str) -> bool:
        principal_ids = [p.id for p in principals]
        target_uri_normalized = target_uri.removeprefix(V1_API_PATH_PREFIX)

        permission_assignments = (
            PermissionAssignmentModel.query.filter(PermissionAssignmentModel.principal_id.in_(principal_ids))
            .filter_by(permission=permission)
            .join(PermissionTargetModel)
            .filter(
                or_(
                    text(f"'{target_uri_normalized}' LIKE permission_target.uri"),
                    # to check for exact matches as well
                    # see test_user_can_access_base_path_when_given_wildcard_permission unit test
                    text(f"'{target_uri_normalized}' = replace(replace(permission_target.uri, '/%', ''), ':%', '')"),
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
                raise Exception(f"Unknown grant type: {permission_assignment.grant_type}")

        return False

    @classmethod
    def user_has_permission(cls, user: UserModel, permission: str, target_uri: str) -> bool:
        if user.principal is None:
            raise MissingPrincipalError(f"Missing principal for user with id: {user.id}")

        principals = [user.principal]

        for group in user.groups:
            if group.principal is None:
                raise MissingPrincipalError(f"Missing principal for group with id: {group.id}")
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
        user_group_assignemnt = UserGroupAssignmentModel.query.filter_by(user_id=user.id, group_id=group.id).first()
        if user_group_assignemnt is None:
            user_group_assignemnt = UserGroupAssignmentModel(user_id=user.id, group_id=group.id)
            db.session.add(user_group_assignemnt)
            db.session.commit()

    @classmethod
    def import_permissions_from_yaml_file(cls, user_model: UserModel | None = None) -> AddedPermissionDict:
        group_permissions = cls.parse_permissions_yaml_into_group_info()
        result = cls.add_permissions_from_group_permissions(group_permissions, user_model)
        return result

    @classmethod
    def find_or_create_permission_target(cls, uri: str) -> PermissionTargetModel:
        uri_with_percent = re.sub(r"\*", "%", uri)
        target_uri_normalized = uri_with_percent.removeprefix(V1_API_PATH_PREFIX)
        permission_target: PermissionTargetModel | None = PermissionTargetModel.query.filter_by(
            uri=target_uri_normalized
        ).first()
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
        permission_assignment: PermissionAssignmentModel | None = PermissionAssignmentModel.query.filter_by(
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
        swagger_functions = ["get_json_spec"]
        authentication_exclusion_list = [
            "status",
            "test_raise_error",
            "authentication_begin",
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
            or api_view_function.__name__.startswith("prom")
            or api_view_function.__name__ == "url_info"
            or api_view_function.__name__.startswith("metric")
            or api_view_function.__name__.startswith("console_ui_")
            or api_view_function.__name__ in authentication_exclusion_list
            or api_view_function.__name__ in swagger_functions
            or module == openid_blueprint
            or module == scaffold  # don't check permissions for static assets
        ):
            return True

        return False

    @classmethod
    def get_permission_from_http_method(cls, http_method: str) -> str | None:
        request_method_mapper = {
            "POST": "create",
            "GET": "read",
            "PUT": "update",
            "DELETE": "delete",
        }
        if http_method in request_method_mapper:
            return request_method_mapper[http_method]

        return None

    @classmethod
    def check_for_permission(cls) -> None:
        if cls.should_disable_auth_for_request():
            return None

        if not hasattr(g, "user"):
            raise UserNotLoggedInError(
                "User is not logged in. Please log in",
            )

        if cls.request_is_excluded_from_permission_check():
            return None

        if cls.request_allows_guest_access():
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

        raise NotAuthorizedError(
            (
                f"User {g.user.username} is not authorized to perform requested action:"
                f" {permission_string} - {request.path}"
            ),
        )

    @classmethod
    def request_is_excluded_from_permission_check(cls) -> bool:
        authorization_exclusion_list = ["permissions_check"]
        api_view_function = current_app.view_functions[request.endpoint]
        if api_view_function and api_view_function.__name__ in authorization_exclusion_list:
            return True
        return False

    @classmethod
    def request_allows_guest_access(cls) -> bool:
        if cls.request_is_excluded_from_permission_check():
            return True

        api_view_function = current_app.view_functions[request.endpoint]
        if api_view_function.__name__ in ["task_show", "task_submit", "task_save_draft"]:
            process_instance_id = int(request.path.split("/")[3])
            task_guid = request.path.split("/")[4]
            if TaskModel.task_guid_allows_guest(task_guid, process_instance_id):
                return True
        return False

    @staticmethod
    def decode_auth_token(auth_token: str) -> dict[str, str | None]:
        secret_key = current_app.config.get("SECRET_KEY")
        if secret_key is None:
            raise KeyError("we need current_app.config to have a SECRET_KEY")

        try:
            payload = jwt.decode(auth_token, options={"verify_signature": False})
            return payload
        except jwt.ExpiredSignatureError as exception:
            raise TokenExpiredError(
                "The Authentication token you provided expired and must be renewed.",
            ) from exception
        except jwt.InvalidTokenError as exception:
            raise TokenInvalidError(
                "The Authentication token you provided is invalid. You need a new token. ",
            ) from exception

    @staticmethod
    def assert_user_can_complete_task(
        process_instance_id: int,
        task_guid: str,
        user: UserModel,
    ) -> bool:
        human_task = HumanTaskModel.query.filter_by(
            task_id=task_guid,
            process_instance_id=process_instance_id,
        ).first()
        if human_task is None:
            raise HumanTaskNotFoundError(
                f"Could find an human task with task guid '{task_guid}' for process instance '{process_instance_id}'"
            )

        if human_task.completed:
            raise HumanTaskAlreadyCompletedError(
                f"Human task with task guid '{task_guid}' for process instance '{process_instance_id}' has already"
                " been completed"
            )

        if user not in human_task.potential_owners:
            raise UserDoesNotHaveAccessToTaskError(
                f"User {user.username} does not have access to update"
                f" task'{task_guid}' for process instance"
                f" '{process_instance_id}'"
            )
        return True

    @classmethod
    def create_user_from_sign_in(cls, user_info: dict) -> UserModel:
        """Fields from user_info.

        name, family_name, given_name, middle_name, nickname, preferred_username,
        profile, picture, website, gender, birthdate, zoneinfo, locale,updated_at, email.
        """
        is_new_user = False
        user_attributes = {}

        if "email" in user_info:
            user_attributes["username"] = user_info["email"]
            user_attributes["email"] = user_info["email"]
        else:  # we fall back to the sub, which may be very ugly.
            fallback_username = user_info["sub"] + "@" + user_info["iss"]
            user_attributes["username"] = fallback_username

        if "preferred_username" in user_info:
            user_attributes["display_name"] = user_info["preferred_username"]
        elif "nickname" in user_info:
            user_attributes["display_name"] = user_info["nickname"]
        elif "name" in user_info:
            user_attributes["display_name"] = user_info["name"]

        user_attributes["service"] = user_info["iss"]
        user_attributes["service_id"] = user_info["sub"]

        desired_group_identifiers = None

        if current_app.config["SPIFFWORKFLOW_BACKEND_OPEN_ID_IS_AUTHORITY_FOR_USER_GROUPS"]:
            if "groups" in user_info:
                desired_group_identifiers = user_info["groups"]

        for field_index, tenant_specific_field in enumerate(
            current_app.config["SPIFFWORKFLOW_BACKEND_OPEN_ID_TENANT_SPECIFIC_FIELDS"]
        ):
            if tenant_specific_field in user_info:
                field_number = field_index + 1
                user_attributes[f"tenant_specific_field_{field_number}"] = user_info[tenant_specific_field]

        # example value for service: http://localhost:7002/realms/spiffworkflow (keycloak url)
        user_model = (
            UserModel.query.filter(UserModel.service == user_attributes["service"])
            .filter(UserModel.username == user_attributes["username"])
            .first()
        )
        if user_model is None:
            current_app.logger.debug("create_user in login_return")
            is_new_user = True
            user_model = UserService().create_user(**user_attributes)
        else:
            # Update with the latest information
            user_db_model_changed = False
            for key, value in user_attributes.items():
                current_value = getattr(user_model, key)
                if current_value != value:
                    user_db_model_changed = True
                    setattr(user_model, key, value)
            if user_db_model_changed:
                db.session.add(user_model)
                db.session.commit()

        if desired_group_identifiers is not None:
            if not isinstance(desired_group_identifiers, list):
                current_app.logger.error(
                    f"Invalid groups property in token: {desired_group_identifiers}."
                    "If groups is specified, it must be a list"
                )
            else:
                for desired_group_identifier in desired_group_identifiers:
                    GroupService.add_user_to_group(user_model, desired_group_identifier)
                current_group_identifiers = [g.identifier for g in user_model.groups]
                groups_to_remove_from_user = [
                    item for item in current_group_identifiers if item not in desired_group_identifiers
                ]
                for gtrfu in groups_to_remove_from_user:
                    if gtrfu != current_app.config["SPIFFWORKFLOW_BACKEND_DEFAULT_USER_GROUP"]:
                        GroupService.remove_user_from_group(user_model, gtrfu)

        # this may eventually get too slow.
        # when it does, be careful about backgrounding, because
        # the user will immediately need permissions to use the site.
        # we are also a little apprehensive about pre-creating users
        # before the user signs in, because we won't know things like
        # the external service user identifier.
        cls.import_permissions_from_yaml_file(user_model)

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
        permissions_to_assign: list[PermissionToAssign] = []

        # we were thinking that if you can start an instance, you ought to be able to:
        #   1. view your own instances.
        #   2. view the logs for these instances.
        if permission_set == "start":
            path_prefixes_that_allow_create_access = ["process-instances"]
            for path_prefix in path_prefixes_that_allow_create_access:
                target_uri = f"/{path_prefix}/{process_related_path_segment}"
                permissions_to_assign.append(PermissionToAssign(permission="create", target_uri=target_uri))

            # giving people access to all logs for an instance actually gives them a little bit more access
            # than would be optimal. ideally, you would only be able to view the logs for instances that you started
            # or that you need to approve, etc. we could potentially implement this by adding before filters
            # in the controllers that confirm that you are viewing logs for your instances. i guess you need to check
            # both for-me and NOT for-me URLs for the instance in question to see if you should get access to its logs.
            # if we implemented things this way, there would also be no way to restrict access to logs when you do not
            # restrict access to instances. everything would be inheriting permissions from instances.
            # if we want to really codify this rule, we could change logs from a prefix to a suffix
            #   (just add it to the end of the process instances path).
            # but that makes it harder to change our minds in the future.
            for target_uri in [
                f"/process-instances/for-me/{process_related_path_segment}",
                f"/logs/{process_related_path_segment}",
                f"/logs/typeahead-filter-values/{process_related_path_segment}",
                f"/process-data-file-download/{process_related_path_segment}",
                f"/event-error-details/{process_related_path_segment}",
            ]:
                permissions_to_assign.append(PermissionToAssign(permission="read", target_uri=target_uri))
        else:
            permissions = permission_set.split(",")
            if permission_set == "all":
                permissions = ["create", "read", "update", "delete"]
                for path_segment_dict in PATH_SEGMENTS_FOR_PERMISSION_ALL:
                    target_uri = f"{path_segment_dict['path']}/{process_related_path_segment}"
                    relevant_permissions = path_segment_dict["relevant_permissions"]
                    for permission in relevant_permissions:
                        permissions_to_assign.append(PermissionToAssign(permission=permission, target_uri=target_uri))

            for target_uri in target_uris:
                for permission in permissions:
                    permissions_to_assign.append(PermissionToAssign(permission=permission, target_uri=target_uri))

        return permissions_to_assign

    @classmethod
    def set_basic_permissions(cls) -> list[PermissionToAssign]:
        permissions_to_assign: list[PermissionToAssign] = []
        permissions_to_assign.append(PermissionToAssign(permission="create", target_uri="/active-users/*"))
        permissions_to_assign.append(PermissionToAssign(permission="create", target_uri="/process-instances/for-me"))
        permissions_to_assign.append(PermissionToAssign(permission="create", target_uri="/users/exists/by-username"))
        permissions_to_assign.append(PermissionToAssign(permission="read", target_uri="/connector-proxy/typeahead/*"))
        permissions_to_assign.append(PermissionToAssign(permission="read", target_uri="/debug/version-info"))
        permissions_to_assign.append(PermissionToAssign(permission="read", target_uri="/extensions"))
        permissions_to_assign.append(PermissionToAssign(permission="read", target_uri="/process-groups"))
        permissions_to_assign.append(PermissionToAssign(permission="read", target_uri="/process-models"))
        permissions_to_assign.append(PermissionToAssign(permission="read", target_uri="/processes"))
        permissions_to_assign.append(PermissionToAssign(permission="read", target_uri="/processes/callers/*"))
        permissions_to_assign.append(PermissionToAssign(permission="read", target_uri="/service-tasks"))
        permissions_to_assign.append(PermissionToAssign(permission="read", target_uri="/user-groups/for-current-user"))
        permissions_to_assign.append(PermissionToAssign(permission="read", target_uri="/users/search"))
        permissions_to_assign.append(PermissionToAssign(permission="read", target_uri="/onboarding"))

        permissions_to_assign.append(
            PermissionToAssign(permission="read", target_uri="/process-instances/report-metadata")
        )
        permissions_to_assign.append(
            PermissionToAssign(permission="read", target_uri="/process-instances/find-by-id/*")
        )

        for permission in ["create", "read", "update", "delete"]:
            permissions_to_assign.append(
                PermissionToAssign(permission=permission, target_uri="/process-instances/reports/*")
            )
            permissions_to_assign.append(PermissionToAssign(permission=permission, target_uri="/tasks/*"))
        return permissions_to_assign

    @classmethod
    def set_elevated_permissions(cls) -> list[PermissionToAssign]:
        """This is basically /* without write access to Process Groups and Process Models.

        Useful for admin-like permissions on readonly environments like a production environment.
        """
        permissions_to_assign = cls.set_support_permissions()
        for permission in ["create", "read", "update", "delete"]:
            permissions_to_assign.append(PermissionToAssign(permission=permission, target_uri="/secrets/*"))

        permissions_to_assign.append(PermissionToAssign(permission="read", target_uri="/authentications"))
        permissions_to_assign.append(PermissionToAssign(permission="read", target_uri="/authentication/configuration"))
        permissions_to_assign.append(PermissionToAssign(permission="read", target_uri="/authentication_begin/*"))
        permissions_to_assign.append(
            PermissionToAssign(permission="update", target_uri="/authentication/configuration")
        )

        permissions_to_assign.append(PermissionToAssign(permission="create", target_uri="/service-accounts"))

        return permissions_to_assign

    @classmethod
    def set_support_permissions(cls) -> list[PermissionToAssign]:
        """Just like elevated permissions minus access to secrets."""
        permissions_to_assign = cls.set_basic_permissions()
        for process_instance_action in ["resume", "terminate", "suspend", "reset"]:
            permissions_to_assign.append(
                PermissionToAssign(permission="create", target_uri=f"/process-instance-{process_instance_action}/*")
            )

        # FIXME: we need to fix so that user that can start a process-model
        # can also start through messages as well
        permissions_to_assign.append(PermissionToAssign(permission="create", target_uri="/messages/*"))
        permissions_to_assign.append(PermissionToAssign(permission="read", target_uri="/messages"))

        permissions_to_assign.append(
            PermissionToAssign(permission="create", target_uri="/can-run-privileged-script/*")
        )
        permissions_to_assign.append(PermissionToAssign(permission="create", target_uri="/debug/*"))
        permissions_to_assign.append(PermissionToAssign(permission="create", target_uri="/send-event/*"))
        permissions_to_assign.append(PermissionToAssign(permission="create", target_uri="/task-complete/*"))
        permissions_to_assign.append(PermissionToAssign(permission="create", target_uri="/extensions/*"))
        permissions_to_assign.append(PermissionToAssign(permission="read", target_uri="/extensions-get-data/*"))

        # read comes from PG and PM ALL permissions as well
        permissions_to_assign.append(PermissionToAssign(permission="create", target_uri="/task-assign/*"))
        permissions_to_assign.append(PermissionToAssign(permission="update", target_uri="/task-data/*"))
        permissions_to_assign.append(PermissionToAssign(permission="read", target_uri="/event-error-details/*"))
        permissions_to_assign.append(PermissionToAssign(permission="read", target_uri="/logs/*"))
        permissions_to_assign.append(PermissionToAssign(permission="read", target_uri="/process-data-file-download/*"))
        permissions_to_assign.append(PermissionToAssign(permission="read", target_uri="/process-data/*"))
        permissions_to_assign.append(PermissionToAssign(permission="read", target_uri="/task-data/*"))

        for permission in ["create", "read", "update", "delete"]:
            permissions_to_assign.append(PermissionToAssign(permission=permission, target_uri="/process-instances/*"))

        permissions_to_assign.append(PermissionToAssign(permission="read", target_uri="/data-stores/*"))
        return permissions_to_assign

    @classmethod
    def set_process_group_permissions(cls, target: str, permission_set: str) -> list[PermissionToAssign]:
        permissions_to_assign: list[PermissionToAssign] = []
        process_group_identifier = target.removeprefix("PG:").replace("/", ":").removeprefix(":")
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
    def set_process_model_permissions(cls, target: str, permission_set: str) -> list[PermissionToAssign]:
        permissions_to_assign: list[PermissionToAssign] = []
        process_model_identifier = target.removeprefix("PM:").replace("/", ":").removeprefix(":")
        process_related_path_segment = f"{process_model_identifier}/*"

        if process_model_identifier == "ALL":
            process_related_path_segment = "*"

        target_uris = [f"/process-models/{process_related_path_segment}"]
        permissions_to_assign = permissions_to_assign + cls.get_permissions_to_assign(
            permission_set, process_related_path_segment, target_uris
        )
        return permissions_to_assign

    @classmethod
    def explode_permissions(cls, permission_set: str, target: str) -> list[PermissionToAssign]:
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
            ELEVATED
                * Operations that require elevated permissions
            SUPPORT
                * Like elevated minus access to secrets

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
            permissions_to_assign += cls.set_process_group_permissions(target, permission_set)
        elif target.startswith("PM:"):
            permissions_to_assign += cls.set_process_model_permissions(target, permission_set)
        elif permission_set == "start":
            raise InvalidPermissionError("Permission 'start' is only available for macros PM and PG.")

        elif target.startswith("BASIC"):
            permissions_to_assign += cls.set_basic_permissions()
        elif target.startswith("ELEVATED"):
            permissions_to_assign += cls.set_elevated_permissions()
        elif target.startswith("SUPPORT"):
            permissions_to_assign += cls.set_support_permissions()
        elif target == "ALL":
            for permission in permissions:
                permissions_to_assign.append(PermissionToAssign(permission=permission, target_uri="/*"))
        elif target.startswith("/"):
            for permission in permissions:
                permissions_to_assign.append(PermissionToAssign(permission=permission, target_uri=target))
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
        group = GroupService.find_or_create_group(group_identifier)
        permissions_to_assign = cls.explode_permissions(permission, target)
        permission_assignments = []
        for permission_to_assign in permissions_to_assign:
            permission_target = cls.find_or_create_permission_target(permission_to_assign.target_uri)
            permission_assignments.append(
                cls.create_permission_for_principal(
                    group.principal, permission_target, permission_to_assign.permission
                )
            )
        return permission_assignments

    @classmethod
    def parse_permissions_yaml_into_group_info(cls) -> list[GroupPermissionsDict]:
        if current_app.config["SPIFFWORKFLOW_BACKEND_PERMISSIONS_FILE_NAME"] is None:
            raise (
                PermissionsFileNotSetError(
                    "SPIFFWORKFLOW_BACKEND_PERMISSIONS_FILE_NAME needs to be set in order to import permissions"
                )
            )

        permission_configs = None
        with open(current_app.config["SPIFFWORKFLOW_BACKEND_PERMISSIONS_FILE_ABSOLUTE_PATH"]) as file:
            permission_configs = yaml.safe_load(file)

        group_permissions_by_group: dict[str, GroupPermissionsDict] = {}
        if current_app.config["SPIFFWORKFLOW_BACKEND_DEFAULT_USER_GROUP"]:
            default_group_identifier = current_app.config["SPIFFWORKFLOW_BACKEND_DEFAULT_USER_GROUP"]
            group_permissions_by_group[default_group_identifier] = {
                "name": default_group_identifier,
                "users": [],
                "permissions": [],
            }

        if "groups" in permission_configs:
            for group_identifier, group_config in permission_configs["groups"].items():
                group_info: GroupPermissionsDict = {"name": group_identifier, "users": [], "permissions": []}
                for username in group_config["users"]:
                    group_info["users"].append(username)
                group_permissions_by_group[group_identifier] = group_info

        if "permissions" in permission_configs:
            for _permission_identifier, permission_config in permission_configs["permissions"].items():
                uri = permission_config["uri"]
                for group_identifier in permission_config["groups"]:
                    group_permissions_by_group[group_identifier]["permissions"].append(
                        {"actions": permission_config["allowed_permissions"], "uri": uri}
                    )

        return list(group_permissions_by_group.values())

    @classmethod
    def add_permissions_from_group_permissions(
        cls,
        group_permissions: list[GroupPermissionsDict],
        user_model: UserModel | None = None,
        group_permissions_only: bool = False,
    ) -> AddedPermissionDict:
        unique_user_group_identifiers: set[str] = set()
        user_to_group_identifiers: list[UserToGroupDict] = []
        permission_assignments = []

        default_group = None
        default_group_identifier = current_app.config["SPIFFWORKFLOW_BACKEND_DEFAULT_USER_GROUP"]
        if default_group_identifier:
            default_group = GroupService.find_or_create_group(default_group_identifier)
            unique_user_group_identifiers.add(default_group_identifier)

        for group in group_permissions:
            group_identifier = group["name"]
            GroupService.find_or_create_group(group_identifier)
            if not group_permissions_only:
                for username in group["users"]:
                    if user_model and username != user_model.username:
                        continue
                    user_to_group_dict: UserToGroupDict = {
                        "username": username,
                        "group_identifier": group_identifier,
                    }
                    user_to_group_identifiers.append(user_to_group_dict)
                    GroupService.add_user_to_group_or_add_to_waiting(username, group_identifier)
                    unique_user_group_identifiers.add(group_identifier)
        for group in group_permissions:
            group_identifier = group["name"]
            if user_model and group_identifier not in unique_user_group_identifiers:
                continue
            for permission in group["permissions"]:
                for crud_op in permission["actions"]:
                    permission_assignments.extend(
                        cls.add_permission_from_uri_or_macro(
                            group_identifier=group_identifier,
                            target=permission["uri"],
                            permission=crud_op,
                        )
                    )
                    unique_user_group_identifiers.add(group_identifier)

        if not group_permissions_only and default_group is not None:
            if user_model:
                cls.associate_user_with_group(user_model, default_group)
            else:
                for user in UserModel.query.filter(UserModel.username.not_in([SPIFF_GUEST_USER])).all():  # type: ignore
                    cls.associate_user_with_group(user, default_group)

        return {
            "group_identifiers": unique_user_group_identifiers,
            "permission_assignments": permission_assignments,
            "user_to_group_identifiers": user_to_group_identifiers,
        }

    @classmethod
    def remove_old_permissions_from_added_permissions(
        cls,
        added_permissions: AddedPermissionDict,
        initial_permission_assignments: list[PermissionAssignmentModel],
        initial_user_to_group_assignments: list[UserGroupAssignmentModel],
        group_permissions_only: bool = False,
    ) -> None:
        added_permission_assignments = added_permissions["permission_assignments"]
        added_group_identifiers = added_permissions["group_identifiers"]
        added_user_to_group_identifiers = added_permissions["user_to_group_identifiers"]

        for ipa in initial_permission_assignments:
            if ipa not in added_permission_assignments:
                db.session.delete(ipa)

        if not group_permissions_only:
            for iutga in initial_user_to_group_assignments:
                # do not remove users from the default user group
                if (
                    current_app.config["SPIFFWORKFLOW_BACKEND_DEFAULT_USER_GROUP"] is None
                    or current_app.config["SPIFFWORKFLOW_BACKEND_DEFAULT_USER_GROUP"] != iutga.group.identifier
                ) and (iutga.group.identifier != SPIFF_GUEST_GROUP and iutga.user.username != SPIFF_GUEST_USER):
                    current_user_dict: UserToGroupDict = {
                        "username": iutga.user.username,
                        "group_identifier": iutga.group.identifier,
                    }
                    if current_user_dict not in added_user_to_group_identifiers:
                        db.session.delete(iutga)

        # do not remove the default user group
        added_group_identifiers.add(current_app.config["SPIFFWORKFLOW_BACKEND_DEFAULT_USER_GROUP"])
        added_group_identifiers.add(SPIFF_GUEST_GROUP)
        groups_to_delete = GroupModel.query.filter(GroupModel.identifier.not_in(added_group_identifiers)).all()
        for gtd in groups_to_delete:
            db.session.delete(gtd)
        db.session.commit()

    @classmethod
    def refresh_permissions(
        cls, group_permissions: list[GroupPermissionsDict], group_permissions_only: bool = False
    ) -> None:
        """Adds new permission assignments and deletes old ones."""
        initial_permission_assignments = (
            PermissionAssignmentModel.query.outerjoin(
                PrincipalModel,
                and_(PrincipalModel.id == PermissionAssignmentModel.principal_id, PrincipalModel.user_id.is_not(None)),
            )
            .outerjoin(UserModel, UserModel.id == PrincipalModel.user_id)
            .filter(or_(UserModel.id.is_(None), UserModel.service != SPIFF_SERVICE_ACCOUNT_AUTH_SERVICE))  # type: ignore
            .all()
        )
        initial_user_to_group_assignments = UserGroupAssignmentModel.query.all()
        group_permissions = group_permissions + cls.parse_permissions_yaml_into_group_info()
        added_permissions = cls.add_permissions_from_group_permissions(
            group_permissions, group_permissions_only=group_permissions_only
        )
        cls.remove_old_permissions_from_added_permissions(
            added_permissions,
            initial_permission_assignments,
            initial_user_to_group_assignments,
            group_permissions_only=group_permissions_only,
        )
