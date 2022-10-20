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
from sqlalchemy import text

from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.permission_assignment import PermissionAssignmentModel
from spiffworkflow_backend.models.permission_target import PermissionTargetModel
from spiffworkflow_backend.models.principal import MissingPrincipalError
from spiffworkflow_backend.models.principal import PrincipalModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.models.user import UserNotFoundError
from spiffworkflow_backend.models.user_group_assignment import UserGroupAssignmentModel
from spiffworkflow_backend.services.user_service import UserService


class PermissionsFileNotSetError(Exception):
    """PermissionsFileNotSetError."""


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
                    user_group_assignemnt = UserGroupAssignmentModel.query.filter_by(
                        user_id=user.id, group_id=group.id
                    ).first()
                    if user_group_assignemnt is None:
                        user_group_assignemnt = UserGroupAssignmentModel(
                            user_id=user.id, group_id=group.id
                        )
                        db.session.add(user_group_assignemnt)
                        db.session.commit()

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
                            principal = (
                                PrincipalModel.query.join(UserModel)
                                .filter(UserModel.username == username)
                                .first()
                            )
                            cls.create_permission_for_principal(
                                principal, permission_target, allowed_permission
                            )

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
            or api_view_function.__name__ in authentication_exclusion_list
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
            message="User is not authorized to perform requested action.",
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

    # def get_bearer_token_from_internal_token(self, internal_token):
    #     """Get_bearer_token_from_internal_token."""
    #     self.decode_auth_token(internal_token)
    #     print(f"get_user_by_internal_token: {internal_token}")

    # def introspect_token(self, basic_token: str) -> dict:
    #     """Introspect_token."""
    #     (
    #         open_id_server_url,
    #         open_id_client_id,
    #         open_id_realm_name,
    #         open_id_client_secret_key,
    #     ) = AuthorizationService.get_open_id_args()
    #
    #     bearer_token = AuthorizationService().get_bearer_token(basic_token)
    #     auth_bearer_string = f"Bearer {bearer_token['access_token']}"
    #
    #     headers = {
    #         "Content-Type": "application/x-www-form-urlencoded",
    #         "Authorization": auth_bearer_string,
    #     }
    #     data = {
    #         "client_id": open_id_client_id,
    #         "client_secret": open_id_client_secret_key,
    #         "token": basic_token,
    #     }
    #     request_url = f"{open_id_server_url}/realms/{open_id_realm_name}/protocol/openid-connect/token/introspect"
    #
    #     introspect_response = requests.post(request_url, headers=headers, data=data)
    #     introspection = json.loads(introspect_response.text)
    #
    #     return introspection

    # def get_permission_by_basic_token(self, basic_token: dict) -> list:
    #     """Get_permission_by_basic_token."""
    #     (
    #         open_id_server_url,
    #         open_id_client_id,
    #         open_id_realm_name,
    #         open_id_client_secret_key,
    #     ) = AuthorizationService.get_open_id_args()
    #
    #     # basic_token = AuthorizationService().refresh_token(basic_token)
    #     # bearer_token = AuthorizationService().get_bearer_token(basic_token['access_token'])
    #     bearer_token = AuthorizationService().get_bearer_token(basic_token)
    #     # auth_bearer_string = f"Bearer {bearer_token['access_token']}"
    #     auth_bearer_string = f"Bearer {bearer_token}"
    #
    #     headers = {
    #         "Content-Type": "application/x-www-form-urlencoded",
    #         "Authorization": auth_bearer_string,
    #     }
    #     data = {
    #         "client_id": open_id_client_id,
    #         "client_secret": open_id_client_secret_key,
    #         "grant_type": "urn:ietf:params:oauth:grant-type:uma-ticket",
    #         "response_mode": "permissions",
    #         "audience": open_id_client_id,
    #         "response_include_resource_name": True,
    #     }
    #     request_url = f"{open_id_server_url}/realms/{open_id_realm_name}/protocol/openid-connect/token"
    #     permission_response = requests.post(request_url, headers=headers, data=data)
    #     permission = json.loads(permission_response.text)
    #     return permission

    # def get_auth_status_for_resource_and_scope_by_token(
    #     self, basic_token: dict, resource: str, scope: str
    # ) -> str:
    #     """Get_auth_status_for_resource_and_scope_by_token."""
    #     (
    #         open_id_server_url,
    #         open_id_client_id,
    #         open_id_realm_name,
    #         open_id_client_secret_key,
    #     ) = AuthorizationService.get_open_id_args()
    #
    #     # basic_token = AuthorizationService().refresh_token(basic_token)
    #     bearer_token = AuthorizationService().get_bearer_token(basic_token)
    #     auth_bearer_string = f"Bearer {bearer_token['access_token']}"
    #
    #     headers = {
    #         "Content-Type": "application/x-www-form-urlencoded",
    #         "Authorization": auth_bearer_string,
    #     }
    #     data = {
    #         "client_id": open_id_client_id,
    #         "client_secret": open_id_client_secret_key,
    #         "grant_type": "urn:ietf:params:oauth:grant-type:uma-ticket",
    #         "permission": f"{resource}#{scope}",
    #         "response_mode": "permissions",
    #         "audience": open_id_client_id,
    #     }
    #     request_url = f"{open_id_server_url}/realms/{open_id_realm_name}/protocol/openid-connect/token"
    #     auth_response = requests.post(request_url, headers=headers, data=data)
    #
    #     print("get_auth_status_for_resource_and_scope_by_token")
    #     auth_status: str = json.loads(auth_response.text)
    #     return auth_status

    # def get_permissions_by_token_for_resource_and_scope(
    #     self, basic_token: str, resource: str|None=None, scope: str|None=None
    # ) -> str:
    #     """Get_permissions_by_token_for_resource_and_scope."""
    #     (
    #         open_id_server_url,
    #         open_id_client_id,
    #         open_id_realm_name,
    #         open_id_client_secret_key,
    #     ) = AuthorizationService.get_open_id_args()
    #
    #     # basic_token = AuthorizationService().refresh_token(basic_token)
    #     # bearer_token = AuthorizationService().get_bearer_token(basic_token['access_token'])
    #     bearer_token = AuthorizationService().get_bearer_token(basic_token)
    #     auth_bearer_string = f"Bearer {bearer_token['access_token']}"
    #
    #     headers = {
    #         "Content-Type": "application/x-www-form-urlencoded",
    #         "Authorization": auth_bearer_string,
    #     }
    #     permision = ""
    #     if resource is not None and resource != '':
    #         permision += resource
    #     if scope is not None and scope != '':
    #         permision += "#" + scope
    #     data = {
    #         "client_id": open_id_client_id,
    #         "client_secret": open_id_client_secret_key,
    #         "grant_type": "urn:ietf:params:oauth:grant-type:uma-ticket",
    #         "response_mode": "permissions",
    #         "permission": permision,
    #         "audience": open_id_client_id,
    #         "response_include_resource_name": True,
    #     }
    #     request_url = f"{open_id_server_url}/realms/{open_id_realm_name}/protocol/openid-connect/token"
    #     permission_response = requests.post(request_url, headers=headers, data=data)
    #     permission: str = json.loads(permission_response.text)
    #     return permission

    # def get_resource_set(self, public_access_token, uri):
    #     """Get_resource_set."""
    #     (
    #         open_id_server_url,
    #         open_id_client_id,
    #         open_id_realm_name,
    #         open_id_client_secret_key,
    #     ) = AuthorizationService.get_open_id_args()
    #     bearer_token = AuthorizationService().get_bearer_token(public_access_token)
    #     auth_bearer_string = f"Bearer {bearer_token['access_token']}"
    #     headers = {
    #         "Content-Type": "application/json",
    #         "Authorization": auth_bearer_string,
    #     }
    #     data = {
    #         "matchingUri": "true",
    #         "deep": "true",
    #         "max": "-1",
    #         "exactName": "false",
    #         "uri": uri,
    #     }
    #
    #     # f"matchingUri=true&deep=true&max=-1&exactName=false&uri={URI_TO_TEST_AGAINST}"
    #     request_url = f"{open_id_server_url}/realms/{open_id_realm_name}/authz/protection/resource_set"
    #     response = requests.get(request_url, headers=headers, data=data)
    #
    #     print("get_resource_set")

    # def get_permission_by_token(self, public_access_token: str) -> dict:
    #     """Get_permission_by_token."""
    #     # TODO: Write a test for this
    #     (
    #         open_id_server_url,
    #         open_id_client_id,
    #         open_id_realm_name,
    #         open_id_client_secret_key,
    #     ) = AuthorizationService.get_open_id_args()
    #     bearer_token = AuthorizationService().get_bearer_token(public_access_token)
    #     auth_bearer_string = f"Bearer {bearer_token['access_token']}"
    #     headers = {
    #         "Content-Type": "application/x-www-form-urlencoded",
    #         "Authorization": auth_bearer_string,
    #     }
    #     data = {
    #         "grant_type": "urn:ietf:params:oauth:grant-type:uma-ticket",
    #         "audience": open_id_client_id,
    #     }
    #     request_url = f"{open_id_server_url}/realms/{open_id_realm_name}/protocol/openid-connect/token"
    #     permission_response = requests.post(request_url, headers=headers, data=data)
    #     permission: dict = json.loads(permission_response.text)
    #
    #     return permission


class KeycloakAuthorization:
    """Interface with Keycloak server."""


# class KeycloakClient:
