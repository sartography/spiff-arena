import inspect
import re
from dataclasses import dataclass
from typing import Any

import yaml
from flask import current_app
from flask import g
from flask import request
from sqlalchemy import and_
from sqlalchemy import func
from sqlalchemy import literal
from sqlalchemy import or_

from spiffworkflow_backend.exceptions.error import HumanTaskAlreadyCompletedError
from spiffworkflow_backend.exceptions.error import HumanTaskNotFoundError
from spiffworkflow_backend.exceptions.error import InvalidPermissionError
from spiffworkflow_backend.exceptions.error import NotAuthorizedError
from spiffworkflow_backend.exceptions.error import PermissionsFileNotSetError
from spiffworkflow_backend.exceptions.error import UserDoesNotHaveAccessToTaskError
from spiffworkflow_backend.exceptions.error import UserNotLoggedInError
from spiffworkflow_backend.helpers.api_version import remove_api_prefix
from spiffworkflow_backend.interfaces import AddedPermissionDict
from spiffworkflow_backend.interfaces import GroupPermissionsDict
from spiffworkflow_backend.interfaces import UserToGroupDict
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.group import SPIFF_GUEST_GROUP
from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.permission_assignment import PermissionAssignmentModel
from spiffworkflow_backend.models.permission_target import PermissionTargetModel
from spiffworkflow_backend.models.principal import PrincipalModel
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.models.service_account import SPIFF_SERVICE_ACCOUNT_AUTH_SERVICE
from spiffworkflow_backend.models.task import TaskModel  # noqa: F401
from spiffworkflow_backend.models.user import SPIFF_GUEST_USER
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.models.user_group_assignment import UserGroupAssignmentModel
from spiffworkflow_backend.models.user_group_assignment_waiting import UserGroupAssignmentWaitingModel
from spiffworkflow_backend.routes.openid_blueprint import openid_blueprint
from spiffworkflow_backend.services.user_service import UserService


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
    {"path": "/message-models", "relevant_permissions": ["read"]},
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
    {"path": "/process-instance-events", "relevant_permissions": ["read"]},
    {"path": "/process-instance-migrate", "relevant_permissions": ["create"]},
    {"path": "/process-instance-run", "relevant_permissions": ["create"]},
    {"path": "/process-instance-suspend", "relevant_permissions": ["create"]},
    {"path": "/process-instance-terminate", "relevant_permissions": ["create"]},
    {"path": "/process-model-import", "relevant_permissions": ["create"]},
    {"path": "/process-model-natural-language", "relevant_permissions": ["create"]},
    {"path": "/process-model-publish", "relevant_permissions": ["create"]},
    {"path": "/process-model-tests/create", "relevant_permissions": ["create"]},
    {"path": "/process-model-tests/run", "relevant_permissions": ["create"]},
    {"path": "/task-assign", "relevant_permissions": ["create"]},
    {"path": "/task-data", "relevant_permissions": ["read", "update"]},
]

# these are api calls that are allowed to generate a public jwt when called
PUBLIC_AUTHENTICATION_EXCLUSION_LIST = [
    "spiffworkflow_backend.routes.public_controller.form_show",
    "spiffworkflow_backend.routes.public_controller.message_form_show",
    "spiffworkflow_backend.routes.public_controller.message_form_submit",
]


class AuthorizationService:
    """Determine whether a user has permission to perform their request."""

    @classmethod
    def has_permission(cls, principals: list[PrincipalModel], permission: str, target_uri: str) -> bool:
        principal_ids = [p.id for p in principals]
        target_uri_normalized = remove_api_prefix(target_uri)

        permission_assignments = (
            PermissionAssignmentModel.query.filter(PermissionAssignmentModel.principal_id.in_(principal_ids))
            .filter_by(permission=permission)
            .join(PermissionTargetModel)
            .filter(
                or_(
                    # found from https://stackoverflow.com/a/46783555
                    literal(target_uri_normalized).like(PermissionTargetModel.uri),
                    # to check for exact matches as well
                    # see test_user_can_access_base_path_when_given_wildcard_permission unit test
                    func.REPLACE(func.REPLACE(PermissionTargetModel.uri, "/%", ""), ":%", "") == target_uri_normalized,
                )
            )
            .all()
        )

        if len(permission_assignments) == 0:
            return False

        all_permissions_permit = True
        for permission_assignment in permission_assignments:
            if permission_assignment.grant_type == "permit":
                pass
            elif permission_assignment.grant_type == "deny":
                all_permissions_permit = False
            else:
                raise Exception(f"Unknown grant type: {permission_assignment.grant_type}")

        return all_permissions_permit

    @classmethod
    def user_has_permission(cls, user: UserModel, permission: str, target_uri: str) -> bool:
        principals = UserService.all_principals_for_user(user)
        return cls.has_permission(principals, permission, target_uri)

    @classmethod
    def all_permission_assignments_for_user(cls, user: UserModel) -> list[PermissionAssignmentModel]:
        principals = UserService.all_principals_for_user(user)
        principal_ids = [p.id for p in principals]
        permission_assignments: list[PermissionAssignmentModel] = (
            PermissionAssignmentModel.query.filter(PermissionAssignmentModel.principal_id.in_(principal_ids))
            .options(db.joinedload(PermissionAssignmentModel.permission_target))
            .all()
        )
        return permission_assignments

    @classmethod
    def permission_assignments_include(
        cls, permission_assignments: list[PermissionAssignmentModel], permission: str, target_uri: str
    ) -> bool:
        uri_with_percent = re.sub(r"\*", "%", target_uri)
        target_uri_normalized = remove_api_prefix(uri_with_percent)

        matching_permission_assignments = []
        for permission_assignment in permission_assignments:
            if permission_assignment.permission == permission and cls.target_uri_matches_actual_uri(
                permission_assignment.permission_target.uri, target_uri_normalized
            ):
                matching_permission_assignments.append(permission_assignment)

        return cls.has_permissions_and_all_permissions_permit(matching_permission_assignments)

    @classmethod
    def has_permissions_and_all_permissions_permit(cls, permission_assignments: list[PermissionAssignmentModel]) -> bool:
        if len(permission_assignments) == 0:
            return False

        for permission_assignment in permission_assignments:
            if permission_assignment.grant_type == "deny":
                return False
        return True

    @classmethod
    def target_uri_matches_actual_uri(cls, target_uri: str, actual_uri: str) -> bool:
        if target_uri.endswith("%"):
            target_uri_without_wildcard = target_uri.removesuffix("%")
            target_uri_without_wildcard_and_without_delimiters = target_uri_without_wildcard.removesuffix(":").removesuffix("/")
            return actual_uri == target_uri_without_wildcard_and_without_delimiters or actual_uri.startswith(
                target_uri_without_wildcard
            )
        return actual_uri == target_uri

    @classmethod
    def delete_all_permissions(cls) -> None:
        """Delete_all_permissions_and_recreate.  EXCEPT For permissions for the current user?"""
        for model in [PermissionAssignmentModel, PermissionTargetModel]:
            db.session.query(model).delete()

        # cascading to principals doesn't seem to work when attempting to delete all so do it like this instead
        for group in GroupModel.query.all():
            db.session.delete(group)
        db.session.commit()

    # if you have access to PG:hey:%, you should be able to see PG hey, obviously.
    # if you have access to PG:hey:yo:%, you should ALSO be able to see PG hey, because that allows you to navigate to hey:yo.
    # if you have access to PG:hey:%, you should be able to see PG hey:yo, but that is handled by the normal permissions system,
    # and we will never ask that question of this method.
    @classmethod
    def is_user_allowed_to_view_process_group_with_id(cls, user: UserModel, group_identifier: str) -> bool:
        modified_group_identifier = ProcessModelInfo.modify_process_identifier_for_path_param(group_identifier)
        has_permission = cls.user_has_permission(
            user=user,
            permission="read",
            target_uri=f"/process-groups/{modified_group_identifier}",
        )
        if has_permission:
            return True
        all_permission_assignments = cls.all_permission_assignments_for_user(user)
        matching_permission_assignments = []
        for permission_assignment in all_permission_assignments:
            uri = permission_assignment.permission_target.uri
            uri_as_pg_identifier = uri.removeprefix("/process-groups/").removesuffix(":%")
            if permission_assignment.permission == "read" and (
                permission_assignment.grant_type == "permit"
                and (
                    uri.startswith(f"/process-groups/{modified_group_identifier}")
                    or uri.startswith(f"/process-models/{modified_group_identifier}")
                )
                or (permission_assignment.grant_type == "deny" and modified_group_identifier.startswith(uri_as_pg_identifier))
            ):
                matching_permission_assignments.append(permission_assignment)
        return cls.has_permissions_and_all_permissions_permit(matching_permission_assignments)

    @classmethod
    def import_permissions_from_yaml_file(cls, user_model: UserModel | None = None) -> AddedPermissionDict:
        group_permissions = cls.parse_permissions_yaml_into_group_info()
        result = cls.add_permissions_from_group_permissions(group_permissions, user_model)
        return result

    @classmethod
    def find_or_create_permission_target(cls, uri: str) -> PermissionTargetModel:
        uri_with_percent = re.sub(r"\*", "%", uri)
        target_uri_normalized = remove_api_prefix(uri_with_percent)
        permission_target: PermissionTargetModel | None = PermissionTargetModel.query.filter_by(uri=target_uri_normalized).first()
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
        grant_type: str = "permit",
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
                grant_type=grant_type,
            )
            db.session.add(permission_assignment)
            db.session.commit()
        elif permission_assignment.grant_type != grant_type:
            permission_assignment.grant_type = grant_type
            db.session.add(permission_assignment)
            db.session.commit()
        return permission_assignment

    @classmethod
    def get_fully_qualified_api_function_from_request(cls) -> tuple[str | None, Any]:
        api_view_function = current_app.view_functions[request.endpoint]
        module = inspect.getmodule(api_view_function)
        api_function_name = api_view_function.__name__ if api_view_function else None
        controller_name = module.__name__ if module is not None else None
        function_full_path = None
        if api_function_name:
            function_full_path = f"{controller_name}.{api_function_name}"
        return (function_full_path, module)

    @classmethod
    def authentication_exclusion_list(cls) -> list:
        authentication_exclusion_list = [
            "spiffworkflow_backend.routes.authentication_controller.authentication_options",
            "spiffworkflow_backend.routes.authentication_controller.login",
            "spiffworkflow_backend.routes.authentication_controller.login_return",
            "spiffworkflow_backend.routes.authentication_controller.login_with_access_token",
            "spiffworkflow_backend.routes.authentication_controller.logout",
            "spiffworkflow_backend.routes.authentication_controller.logout_return",
            "spiffworkflow_backend.routes.debug_controller.test_raise_error",
            "spiffworkflow_backend.routes.debug_controller.url_info",
            "spiffworkflow_backend.routes.debug_controller.process_instance_with_most_tasks",
            "spiffworkflow_backend.routes.health_controller.status",
            "spiffworkflow_backend.routes.service_tasks_controller.authentication_begin",
            "spiffworkflow_backend.routes.service_tasks_controller.authentication_callback",
            "spiffworkflow_backend.routes.tasks_controller.task_allows_guest",
            "spiffworkflow_backend.routes.webhooks_controller.github_webhook_receive",
            "spiffworkflow_backend.routes.webhooks_controller.webhook",
            "flask.blueprints.send_static_file",
            # swagger api calls
            "connexion.apis.flask_api.console_ui_home",
            "connexion.apis.flask_api.console_ui_static_files",
            "connexion.apis.flask_api.get_json_spec",
        ]
        if not current_app.config["SPIFFWORKFLOW_BACKEND_USE_AUTH_FOR_METRICS"]:
            authentication_exclusion_list.append("prometheus_flask_exporter.prometheus_metrics")
        return authentication_exclusion_list

    @classmethod
    def should_disable_auth_for_request(cls) -> bool:
        if request.method == "OPTIONS":
            return True

        # if the endpoint does not exist then let the system 404
        #
        # for some reason this runs before connexion checks if the
        # endpoint exists.
        if not request.endpoint:
            return True

        api_function_full_path, module = cls.get_fully_qualified_api_function_from_request()
        if (
            api_function_full_path
            and (api_function_full_path in cls.authentication_exclusion_list())
            or module == openid_blueprint
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
    def check_permission_for_request(cls) -> None:
        permission_string = cls.get_permission_from_http_method(request.method)
        if permission_string:
            has_permission = cls.user_has_permission(
                user=g.user,
                permission=permission_string,
                target_uri=request.path,
            )
            if has_permission:
                return None

        raise NotAuthorizedError(
            f"User {g.user.username} is not authorized to perform requested action: {permission_string} - {request.path}",
        )

    @classmethod
    def check_for_permission(cls, decoded_token: dict | None) -> None:
        if cls.should_disable_auth_for_request():
            return None

        if not hasattr(g, "user"):
            raise UserNotLoggedInError(
                "User is not logged in. Please log in",
            )

        if cls.request_is_excluded_from_permission_check():
            return None
        if cls.request_is_excluded_from_public_user_permission_check(decoded_token):
            return None

        cls.check_permission_for_request()

    @classmethod
    def request_is_excluded_from_permission_check(cls) -> bool:
        authorization_exclusion_list = [
            "spiffworkflow_backend.routes.process_api_blueprint.permissions_check",
            "spiffworkflow_backend.routes.process_groups_controller.process_group_show",
        ]
        api_function_full_path, module = cls.get_fully_qualified_api_function_from_request()
        if api_function_full_path and (api_function_full_path in authorization_exclusion_list):
            return True

        return False

    @classmethod
    def request_is_excluded_from_public_user_permission_check(cls, decoded_token: dict | None) -> bool:
        authorization_exclusion_for_public_user_list = [
            "spiffworkflow_backend.routes.connector_proxy_controller.typeahead",
        ]
        api_function_full_path, module = cls.get_fully_qualified_api_function_from_request()
        if (
            api_function_full_path
            and (api_function_full_path in authorization_exclusion_for_public_user_list)
            and decoded_token
            and "public" in decoded_token
            and decoded_token["public"] is True
        ):
            return True

        return False

    @staticmethod
    def assert_user_can_complete_human_task(
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
                f"Human task with task guid '{task_guid}' for process instance '{process_instance_id}' has already been completed"
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
        new_group_ids: set[int] = set()
        old_group_ids: set[int] = set()
        user_attributes = {}

        if "preferred_username" in user_info:
            user_attributes["username"] = user_info["preferred_username"]
        elif "email" in user_info:
            user_attributes["username"] = user_info["email"]
        else:
            user_attributes["username"] = f"{user_info['sub']}@{user_info['iss']}"

        if "preferred_username" in user_info:
            user_attributes["display_name"] = user_info["preferred_username"]
        elif "nickname" in user_info:
            user_attributes["display_name"] = user_info["nickname"]
        elif "name" in user_info:
            user_attributes["display_name"] = user_info["name"]

        user_attributes["email"] = user_info.get("email")
        user_attributes["service"] = user_info["iss"]
        user_attributes["service_id"] = user_info["sub"]

        desired_group_identifiers = None

        if current_app.config["SPIFFWORKFLOW_BACKEND_OPEN_ID_IS_AUTHORITY_FOR_USER_GROUPS"]:
            desired_group_identifiers = []
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
            .filter(UserModel.service_id == user_attributes["service_id"])
            .first()
        )
        new_user = False
        if user_model is None:
            current_app.logger.debug("create_user in login_return")
            user_model = UserService().create_user(**user_attributes)
            new_user = True
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
                current_app.logger.error(  # type: ignore
                    f"Invalid groups property in token: {desired_group_identifiers}.If groups is specified, it must be a list"
                )
            else:
                for desired_group_identifier in desired_group_identifiers:
                    new_group = UserService.add_user_to_group_by_group_identifier(
                        user_model, desired_group_identifier, source_is_open_id=True
                    )
                    if new_group is not None:
                        new_group_ids.add(new_group.id)
                group_ids_to_remove_from_user = [
                    item.id for item in user_model.groups if item.identifier not in desired_group_identifiers
                ]
                for group_id in group_ids_to_remove_from_user:
                    if group_id != current_app.config["SPIFFWORKFLOW_BACKEND_DEFAULT_USER_GROUP"]:
                        old_group_ids.add(group_id)
                        UserService.remove_user_from_group(user_model, group_id)

        # Track group IDs before and after YAML import to catch changes from configuration
        group_ids_before_yaml_import = {g.id for g in user_model.groups}

        # this may eventually get too slow.
        # when it does, be careful about backgrounding, because
        # the user will immediately need permissions to use the site.
        # we are also a little apprehensive about pre-creating users
        # before the user signs in, because we won't know things like
        # the external service user identifier.
        cls.import_permissions_from_yaml_file(user_model)

        # Refresh the groups relationship to get the latest from the database
        db.session.expire(user_model, ["groups"])
        # Calculate which groups were added/removed by YAML configuration changes
        group_ids_after_yaml_import = {g.id for g in user_model.groups}
        yaml_added_group_ids = group_ids_after_yaml_import - group_ids_before_yaml_import
        yaml_removed_group_ids = group_ids_before_yaml_import - group_ids_after_yaml_import

        # Combine YAML changes with OpenID changes
        new_group_ids.update(yaml_added_group_ids)
        old_group_ids.update(yaml_removed_group_ids)

        if new_user:
            new_group_ids.update({g.id for g in user_model.groups})

        if len(new_group_ids) > 0 or len(old_group_ids) > 0:
            UserService.update_human_task_assignments_for_user(
                user_model, new_group_ids=new_group_ids, old_group_ids=old_group_ids
            )

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
            for target_uri in [
                f"/process-instances/{process_related_path_segment}",
                f"/process-instance-run/{process_related_path_segment}",
            ]:
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
                f"/process-instance-events/{process_related_path_segment}",
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

        # Default permission to access frontend
        permissions_to_assign.append(PermissionToAssign(permission="read", target_uri="/frontend-access"))

        # gets lists of instances (we use a POST with a json body because there are complex filters, hence the create)
        permissions_to_assign.append(PermissionToAssign(permission="create", target_uri="/process-instances/for-me"))
        # view individual instances that require my attention
        permissions_to_assign.append(PermissionToAssign(permission="read", target_uri="/process-instances/for-me/*"))

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

        permissions_to_assign.append(PermissionToAssign(permission="read", target_uri="/process-instances/report-metadata"))
        permissions_to_assign.append(PermissionToAssign(permission="read", target_uri="/process-instances/find-by-id/*"))

        permissions_to_assign.append(PermissionToAssign(permission="read", target_uri="/script-assist/enabled"))
        permissions_to_assign.append(PermissionToAssign(permission="create", target_uri="/script-assist/process-message"))

        permissions_to_assign.append(PermissionToAssign(permission="read", target_uri="/upsearch-locations"))

        for permission in ["create", "read", "update", "delete"]:
            permissions_to_assign.append(PermissionToAssign(permission=permission, target_uri="/process-instances/reports/*"))
            permissions_to_assign.append(PermissionToAssign(permission=permission, target_uri="/public/*"))
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
        permissions_to_assign.append(PermissionToAssign(permission="update", target_uri="/authentication/configuration"))

        permissions_to_assign.append(PermissionToAssign(permission="create", target_uri="/service-accounts"))

        return permissions_to_assign

    @classmethod
    def set_support_permissions(cls) -> list[PermissionToAssign]:
        """Just like elevated permissions minus access to secrets."""
        permissions_to_assign = cls.set_basic_permissions()
        for process_instance_action in ["migrate", "resume", "terminate", "suspend", "reset"]:
            permissions_to_assign.append(
                PermissionToAssign(permission="create", target_uri=f"/process-instance-{process_instance_action}/*")
            )

        # FIXME: we need to fix so that user that can start a process-model
        # can also start through messages as well
        permissions_to_assign.append(PermissionToAssign(permission="create", target_uri="/messages/*"))
        permissions_to_assign.append(PermissionToAssign(permission="read", target_uri="/messages/*"))
        permissions_to_assign.append(PermissionToAssign(permission="read", target_uri="/messages"))

        permissions_to_assign.append(PermissionToAssign(permission="create", target_uri="/can-run-privileged-script/*"))
        permissions_to_assign.append(PermissionToAssign(permission="create", target_uri="/debug/*"))
        permissions_to_assign.append(PermissionToAssign(permission="create", target_uri="/send-event/*"))
        permissions_to_assign.append(PermissionToAssign(permission="create", target_uri="/task-complete/*"))
        permissions_to_assign.append(PermissionToAssign(permission="create", target_uri="/extensions/*"))
        permissions_to_assign.append(PermissionToAssign(permission="read", target_uri="/extensions-get-data/*"))
        permissions_to_assign.append(PermissionToAssign(permission="read", target_uri="/frontend-access"))

        # read comes from PG and PM ALL permissions as well
        permissions_to_assign.append(PermissionToAssign(permission="create", target_uri="/task-assign/*"))
        permissions_to_assign.append(PermissionToAssign(permission="create", target_uri="/process-instance-run/*"))
        permissions_to_assign.append(PermissionToAssign(permission="update", target_uri="/task-data/*"))
        permissions_to_assign.append(PermissionToAssign(permission="read", target_uri="/event-error-details/*"))
        permissions_to_assign.append(PermissionToAssign(permission="read", target_uri="/logs/*"))
        permissions_to_assign.append(PermissionToAssign(permission="read", target_uri="/process-data-file-download/*"))
        permissions_to_assign.append(PermissionToAssign(permission="read", target_uri="/process-data/*"))
        permissions_to_assign.append(PermissionToAssign(permission="read", target_uri="/process-instance-events/*"))
        permissions_to_assign.append(PermissionToAssign(permission="read", target_uri="/task-data/*"))

        for permission in ["create", "read", "update", "delete"]:
            permissions_to_assign.append(PermissionToAssign(permission=permission, target_uri="/process-instances/*"))

        permissions_to_assign.append(PermissionToAssign(permission="read", target_uri="/data-stores/*"))
        return permissions_to_assign

    @classmethod
    def check_target_is_compatible_with_macro(cls, macro: str, target: str) -> None:
        if macro in ["PM", "PG"] and "*" in target:
            raise InvalidPermissionError(f"Wildcards '*' are not allowed in PM and PG macros. '{target}' is invalid.")

    @classmethod
    def set_process_group_permissions(cls, target: str, permission_set: str) -> list[PermissionToAssign]:
        cls.check_target_is_compatible_with_macro("PG", target)
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
        cls.check_target_is_compatible_with_macro("PM", target)
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
        if "," in permission_set:
            raise Exception(f"Found comma in permission_set. This should be an array instead: {permission_set}")
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
        group = UserService.find_or_create_group(group_identifier)
        grant_type = "permit"
        permission_without_deny = permission
        if permission.startswith("DENY:"):
            permission_without_deny = permission.removeprefix("DENY:")
            grant_type = "deny"
        permissions_to_assign = cls.explode_permissions(permission_without_deny, target)
        permission_assignments = []
        for permission_to_assign in permissions_to_assign:
            permission_target = cls.find_or_create_permission_target(permission_to_assign.target_uri)
            permission_assignments.append(
                cls.create_permission_for_principal(
                    principal=group.principal,
                    permission_target=permission_target,
                    permission=permission_to_assign.permission,
                    grant_type=grant_type,
                )
            )
        return permission_assignments

    @classmethod
    def get_permissions_from_config(cls, permission_config: dict) -> list[str]:
        actions = []
        if "actions" in permission_config:
            actions = permission_config["actions"]
        elif "allowed_permissions" in permission_config:
            current_app.logger.warning(
                "DEPRECATION WARNING: found use of 'allowed_permissions' in permissions yaml. Please use 'actions'"
                " instead of 'allowed_permissions' in your config file."
            )
            actions = permission_config["allowed_permissions"]
        return actions

    @classmethod
    def load_permissions_yaml(cls) -> Any:
        if current_app.config["SPIFFWORKFLOW_BACKEND_PERMISSIONS_FILE_ABSOLUTE_PATH"] is None:
            raise (
                PermissionsFileNotSetError(
                    "SPIFFWORKFLOW_BACKEND_PERMISSIONS_FILE_ABSOLUTE_PATH needs to be set in order to import permissions"
                )
            )

        with open(current_app.config["SPIFFWORKFLOW_BACKEND_PERMISSIONS_FILE_ABSOLUTE_PATH"]) as file:
            return yaml.safe_load(file)

    @classmethod
    def parse_permissions_yaml_into_group_info(cls) -> list[GroupPermissionsDict]:
        permission_configs = cls.load_permissions_yaml()

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
                actions = cls.get_permissions_from_config(permission_config)
                for group_identifier in permission_config["groups"]:
                    group_permissions_by_group[group_identifier]["permissions"].append({"actions": actions, "uri": uri})

        return list(group_permissions_by_group.values())

    @classmethod
    def add_permissions_from_group_permissions(
        cls,
        group_permissions: list[GroupPermissionsDict],
        user_model: UserModel | None = None,
        group_permissions_only: bool = False,
    ) -> AddedPermissionDict:
        count = len(group_permissions)
        current_app.logger.debug(
            f"ADD PERMISSIONS - START: Processing {count} group permissions, group_permissions_only={group_permissions_only}"
        )

        unique_user_group_identifiers: set[str] = set()
        user_to_group_identifiers: list[UserToGroupDict] = []
        waiting_user_group_assignments: list[UserGroupAssignmentWaitingModel] = []
        permission_assignments = []

        default_group = None
        default_group_identifier = current_app.config["SPIFFWORKFLOW_BACKEND_DEFAULT_USER_GROUP"]
        if default_group_identifier:
            current_app.logger.debug(f"ADD PERMISSIONS - Finding or creating default group: {default_group_identifier}")
            default_group = UserService.find_or_create_group(default_group_identifier)
            unique_user_group_identifiers.add(default_group_identifier)

        for _group_index, group in enumerate(group_permissions):
            group_identifier = group["name"]
            group_num = _group_index + 1
            group_total = len(group_permissions)
            current_app.logger.debug(f"ADD PERMISSIONS - Processing group {group_num}/{group_total}: {group_identifier}")

            UserService.find_or_create_group(group_identifier)
            if group_identifier == current_app.config["SPIFFWORKFLOW_BACKEND_DEFAULT_PUBLIC_USER_GROUP"]:
                unique_user_group_identifiers.add(group_identifier)

            if not group_permissions_only:
                current_app.logger.debug(
                    f"ADD PERMISSIONS - Processing {len(group['users'])} users for group: {group_identifier}"
                )
                for user_index, username_or_email in enumerate(group["users"]):
                    if user_model and username_or_email not in [user_model.username, user_model.email]:
                        continue

                    user_count = len(group["users"])
                    user_num = user_index + 1
                    current_app.logger.debug(
                        f"ADD PERMISSIONS - Processing user {user_num}/{user_count}: "
                        f"{username_or_email} for group: {group_identifier}"
                    )
                    (wugam, new_user_to_group_identifiers) = UserService.add_user_to_group_or_add_to_waiting(
                        username_or_email, group_identifier
                    )
                    if wugam is not None:
                        waiting_user_group_assignments.append(wugam)
                        current_app.logger.debug(
                            f"ADD PERMISSIONS - Added waiting group assignment for user: {username_or_email}, "
                            f"group: {group_identifier}"
                        )

                    user_to_group_identifiers = user_to_group_identifiers + new_user_to_group_identifiers
                    unique_user_group_identifiers.add(group_identifier)

        for _group_index, group in enumerate(group_permissions):
            group_identifier = group["name"]

            # If we have a user_model, check if they are already a member of this group
            # or if this group is in the unique_user_group_identifiers set
            user_is_member_of_group = False
            if user_model:
                # Check if user is already a member of this group (especially via OIDC)
                if any(g.identifier == group_identifier for g in user_model.groups):
                    user_is_member_of_group = True
                    # Make sure this group is in unique_user_group_identifiers
                    unique_user_group_identifiers.add(group_identifier)
                    current_app.logger.debug(
                        f"ADD PERMISSIONS - User {user_model.username} is already a member of group {group_identifier}"
                    )

            if user_model and not user_is_member_of_group and group_identifier not in unique_user_group_identifiers:
                current_app.logger.debug(
                    f"ADD PERMISSIONS - Skipping permissions for group {group_identifier} - not in unique group identifiers"
                )
                continue

            current_app.logger.debug(
                f"ADD PERMISSIONS - Processing {len(group['permissions'])} permissions for group: {group_identifier}"
            )
            for permission_index, permission in enumerate(group["permissions"]):
                permission_count = len(group["permissions"])
                permission_num = permission_index + 1
                uri = permission["uri"]
                actions = permission["actions"]
                current_app.logger.debug(
                    f"ADD PERMISSIONS - Processing permission {permission_num}/{permission_count} "
                    f"for group: {group_identifier}, uri: {uri}, actions: {actions}"
                )

                for crud_op in permission["actions"]:
                    current_app.logger.debug(
                        f"ADD PERMISSIONS - Adding permission: {crud_op} on {permission['uri']} for group: {group_identifier}"
                    )
                    new_permissions = cls.add_permission_from_uri_or_macro(
                        group_identifier=group_identifier,
                        target=permission["uri"],
                        permission=crud_op,
                    )
                    current_app.logger.debug(f"ADD PERMISSIONS - Added {len(new_permissions)} permission assignments")
                    permission_assignments.extend(new_permissions)
                    unique_user_group_identifiers.add(group_identifier)

        if not group_permissions_only and default_group is not None:
            if user_model:
                current_app.logger.debug(
                    f"ADD PERMISSIONS - Adding user {user_model.username} to default group: {default_group_identifier}"
                )
                UserService.add_user_to_group(user_model, default_group)
            else:
                users = UserModel.query.filter(UserModel.username.not_in([SPIFF_GUEST_USER])).all()  # type: ignore
                current_app.logger.debug(
                    f"ADD PERMISSIONS - Adding {len(users)} users to default group: {default_group_identifier}"
                )
                for user in users:
                    UserService.add_user_to_group(user, default_group)

        result: AddedPermissionDict = {
            "group_identifiers": unique_user_group_identifiers,
            "permission_assignments": permission_assignments,
            "user_to_group_identifiers": user_to_group_identifiers,
            "waiting_user_group_assignments": waiting_user_group_assignments,
        }

        num_permissions = len(permission_assignments)
        num_groups = len(unique_user_group_identifiers)
        current_app.logger.debug(
            f"ADD PERMISSIONS - COMPLETED: Added {num_permissions} permission assignments, {num_groups} unique group identifiers"
        )
        return result

    @classmethod
    def remove_old_permissions_from_added_permissions(
        cls,
        added_permissions: AddedPermissionDict,
        initial_permission_assignments: list[PermissionAssignmentModel],
        initial_user_to_group_assignments: list[UserGroupAssignmentModel],
        initial_waiting_group_assignments: list[UserGroupAssignmentWaitingModel],
        group_permissions_only: bool = False,
    ) -> None:
        added_permission_assignments = added_permissions["permission_assignments"]
        added_user_to_group_identifiers = added_permissions["user_to_group_identifiers"]
        added_waiting_group_assignments = added_permissions["waiting_user_group_assignments"]

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

        for wugam in initial_waiting_group_assignments:
            if wugam not in added_waiting_group_assignments:
                db.session.delete(wugam)

        db.session.commit()

    @classmethod
    def refresh_permissions(cls, group_permissions: list[GroupPermissionsDict], group_permissions_only: bool = False) -> None:
        """Adds new permission assignments and deletes old ones."""
        groups_count = len(group_permissions)
        current_app.logger.debug(
            f"AUTH SERVICE - REFRESH PERMISSIONS - START with {groups_count} group(s), "
            f"group_permissions_only={group_permissions_only}"
        )

        try:
            current_app.logger.debug("AUTH SERVICE - REFRESH PERMISSIONS - Getting initial permission assignments")
            initial_permission_assignments = (
                PermissionAssignmentModel.query.outerjoin(
                    PrincipalModel,
                    and_(PrincipalModel.id == PermissionAssignmentModel.principal_id, PrincipalModel.user_id.is_not(None)),
                )
                .outerjoin(UserModel, UserModel.id == PrincipalModel.user_id)
                .filter(or_(UserModel.id.is_(None), UserModel.service != SPIFF_SERVICE_ACCOUNT_AUTH_SERVICE))  # type: ignore
                .all()
            )
            current_app.logger.debug(
                f"AUTH SERVICE - REFRESH PERMISSIONS - Found {len(initial_permission_assignments)} initial permission assignments"
            )

            current_app.logger.debug("AUTH SERVICE - REFRESH PERMISSIONS - Getting initial user group assignments")
            initial_user_to_group_assignments = UserGroupAssignmentModel.query.all()
            count_assignments = len(initial_user_to_group_assignments)
            current_app.logger.debug(
                f"AUTH SERVICE - REFRESH PERMISSIONS - Found {count_assignments} initial user group assignments"
            )

            current_app.logger.debug("AUTH SERVICE - REFRESH PERMISSIONS - Getting initial waiting group assignments")
            initial_waiting_group_assignments = UserGroupAssignmentWaitingModel.query.all()
            waiting_count = len(initial_waiting_group_assignments)
            current_app.logger.debug(
                f"AUTH SERVICE - REFRESH PERMISSIONS - Found {waiting_count} initial waiting group assignments"
            )

            current_app.logger.debug("AUTH SERVICE - REFRESH PERMISSIONS - Parsing permissions from YAML file")
            parsed_permissions = cls.parse_permissions_yaml_into_group_info()
            current_app.logger.debug(
                f"AUTH SERVICE - REFRESH PERMISSIONS - Parsed {len(parsed_permissions)} group permissions from YAML file"
            )

            group_permissions = group_permissions + parsed_permissions
            current_app.logger.debug(
                f"AUTH SERVICE - REFRESH PERMISSIONS - Total of {len(group_permissions)} group permissions to process"
            )

            current_app.logger.debug("AUTH SERVICE - REFRESH PERMISSIONS - Adding permissions from group permissions")
            added_permissions = cls.add_permissions_from_group_permissions(
                group_permissions, group_permissions_only=group_permissions_only
            )
            perm_count = len(added_permissions["permission_assignments"])
            group_count = len(added_permissions["group_identifiers"])
            current_app.logger.debug(
                f"AUTH SERVICE - REFRESH PERMISSIONS - Added permissions: {perm_count} permission "
                f"assignments, {group_count} group identifiers"
            )

            current_app.logger.debug("AUTH SERVICE - REFRESH PERMISSIONS - Removing old permissions")
            cls.remove_old_permissions_from_added_permissions(
                added_permissions,
                initial_permission_assignments,
                initial_user_to_group_assignments,
                initial_waiting_group_assignments,
                group_permissions_only=group_permissions_only,
            )
            current_app.logger.debug("AUTH SERVICE - REFRESH PERMISSIONS - COMPLETED successfully")

        except Exception as ex:
            current_app.logger.error(f"AUTH SERVICE - REFRESH PERMISSIONS - ERROR: {str(ex)}")
            raise
