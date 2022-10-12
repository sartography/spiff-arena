"""Test_authorization."""
from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestAuthorization(BaseTest):
    """TestAuthorization."""

    # def test_get_bearer_token(self, app: Flask) -> None:
    #     """Test_get_bearer_token."""
    #     for user_id in ("user_1", "user_2", "admin_1", "admin_2"):
    #         public_access_token = self.get_public_access_token(user_id, user_id)
    #         bearer_token = PublicAuthenticationService.get_bearer_token(public_access_token)
    #         assert isinstance(public_access_token, str)
    #         assert isinstance(bearer_token, dict)
    #         assert "access_token" in bearer_token
    #         assert isinstance(bearer_token["access_token"], str)
    #         assert "refresh_token" in bearer_token
    #         assert isinstance(bearer_token["refresh_token"], str)
    #         assert "token_type" in bearer_token
    #         assert bearer_token["token_type"] == "Bearer"
    #         assert "scope" in bearer_token
    #         assert isinstance(bearer_token["scope"], str)
    #
    # def test_get_user_info_from_public_access_token(self, app: Flask) -> None:
    #     """Test_get_user_info_from_public_access_token."""
    #     for user_id in ("user_1", "user_2", "admin_1", "admin_2"):
    #         public_access_token = self.get_public_access_token(user_id, user_id)
    #         user_info = PublicAuthenticationService.get_user_info_from_id_token(
    #             public_access_token
    #         )
    #         assert "sub" in user_info
    #         assert isinstance(user_info["sub"], str)
    #         assert len(user_info["sub"]) == 36
    #         assert "preferred_username" in user_info
    #         assert user_info["preferred_username"] == user_id
    #         assert "email" in user_info
    #         assert user_info["email"] == f"{user_id}@example.com"
    #
    # def test_introspect_token(self, app: Flask) -> None:
    #     """Test_introspect_token."""
    #     (
    #         keycloak_server_url,
    #         keycloak_client_id,
    #         keycloak_realm_name,
    #         keycloak_client_secret_key,
    #     ) = self.get_keycloak_constants(app)
    #     for user_id in ("user_1", "user_2", "admin_1", "admin_2"):
    #         basic_token = self.get_public_access_token(user_id, user_id)
    #         introspection = PublicAuthenticationService.introspect_token(basic_token)
    #         assert isinstance(introspection, dict)
    #         assert introspection["typ"] == "Bearer"
    #         assert introspection["preferred_username"] == user_id
    #         assert introspection["client_id"] == "spiffworkflow-frontend"
    #
    #         assert "resource_access" in introspection
    #         resource_access = introspection["resource_access"]
    #         assert isinstance(resource_access, dict)
    #
    #         assert keycloak_client_id in resource_access
    #         client = resource_access[keycloak_client_id]
    #         assert "roles" in client
    #         roles = client["roles"]
    #
    #         assert isinstance(roles, list)
    #         if user_id == "admin_1":
    #             assert len(roles) == 2
    #             for role in roles:
    #                 assert role in ("User", "Admin")
    #         elif user_id == "admin_2":
    #             assert len(roles) == 1
    #             assert roles[0] == "User"
    #         elif user_id == "user_1" or user_id == "user_2":
    #             assert len(roles) == 2
    #             for role in roles:
    #                 assert role in ("User", "Anonymous")
    #
    # def test_get_permission_by_token(self, app: Flask) -> None:
    #     """Test_get_permission_by_token."""
    #     output: dict = {}
    #     for user_id in ("user_1", "user_2", "admin_1", "admin_2"):
    #         output[user_id] = {}
    #         basic_token = self.get_public_access_token(user_id, user_id)
    #         permissions = PublicAuthenticationService.get_permission_by_basic_token(
    #             basic_token
    #         )
    #         if isinstance(permissions, list):
    #             for permission in permissions:
    #                 resource_name = permission["rsname"]
    #                 output[user_id][resource_name] = {}
    #                 # assert resource_name in resource_names
    #                 # if resource_name == 'Process Groups' or resource_name == 'Process Models':
    #                 if "scopes" in permission:
    #                     scopes = permission["scopes"]
    #                     output[user_id][resource_name]["scopes"] = scopes
    #
    #             # if user_id == 'admin_1':
    #             #     # assert len(permissions) == 3
    #             #     for permission in permissions:
    #             #         resource_name = permission['rsname']
    #             #         # assert resource_name in resource_names
    #             #         if resource_name == 'Process Groups' or resource_name == 'Process Models':
    #             #             # assert len(permission['scopes']) == 4
    #             #             for item in permission['scopes']:
    #             #                 # assert item in ('instantiate', 'read', 'update', 'delete')
    #             #                 ...
    #             #         else:
    #             #             # assert resource_name == 'Default Resource'
    #             #             # assert 'scopes' not in permission
    #             #             ...
    #             #
    #             # if user_id == 'admin_2':
    #             #     # assert len(permissions) == 3
    #             #     for permission in permissions:
    #             #         resource_name = permission['rsname']
    #             #         # assert resource_name in resource_names
    #             #         if resource_name == 'Process Groups' or resource_name == 'Process Models':
    #             #             # assert len(permission['scopes']) == 1
    #             #             # assert permission['scopes'][0] == 'read'
    #             #             ...
    #             #         else:
    #             #             # assert resource_name == 'Default Resource'
    #             #             # assert 'scopes' not in permission
    #             #             ...
    #         # else:
    #         #     print(f"No Permissions: {permissions}")
    #     print("test_get_permission_by_token")
    #
    # def test_get_auth_status_for_resource_and_scope_by_token(self, app: Flask) -> None:
    #     """Test_get_auth_status_for_resource_and_scope_by_token."""
    #     resources = "Admin", "Process Groups", "Process Models"
    #     # scope = 'read'
    #     output: dict = {}
    #     for user_id in ("user_1", "user_2", "admin_1", "admin_2"):
    #         output[user_id] = {}
    #         basic_token = self.get_public_access_token(user_id, user_id)
    #         for resource in resources:
    #             output[user_id][resource] = {}
    #             for scope in "instantiate", "read", "update", "delete":
    #                 auth_status = PublicAuthenticationService.get_auth_status_for_resource_and_scope_by_token(
    #                     basic_token, resource, scope
    #                 )
    #                 output[user_id][resource][scope] = auth_status
    #     print("test_get_auth_status_for_resource_and_scope_by_token")
    #
    # def test_get_permissions_by_token_for_resource_and_scope(self, app: Flask) -> None:
    #     """Test_get_permissions_by_token_for_resource_and_scope."""
    #     resource_names = "Default Resource", "Process Groups", "Process Models"
    #     output: dict = {}
    #     for user_id in ("user_1", "user_2", "admin_1", "admin_2"):
    #         output[user_id] = {}
    #         basic_token = self.get_public_access_token(user_id, user_id)
    #         for resource in resource_names:
    #             output[user_id][resource] = {}
    #             for scope in "instantiate", "read", "update", "delete":
    #                 permissions = PublicAuthenticationService.get_permissions_by_token_for_resource_and_scope(
    #                     basic_token, resource, scope
    #                 )
    #                 output[user_id][resource][scope] = permissions
    #     print("test_get_permissions_by_token_for_resource_and_scope")
