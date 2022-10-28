"""Test_authentication."""
import ast
import base64

from spiffworkflow_backend.services.authentication_service import (
    AuthenticationService,
)
from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestAuthentication(BaseTest):
    """TestAuthentication."""

    def test_get_login_state(self) -> None:
        """Test_get_login_state."""
        redirect_url = "http://example.com/"
        state = AuthenticationService.generate_state(redirect_url)
        state_dict = ast.literal_eval(base64.b64decode(state).decode("utf-8"))

        assert isinstance(state_dict, dict)
        assert "redirect_url" in state_dict.keys()
        assert state_dict["redirect_url"] == redirect_url

    # def test_get_login_redirect_url(self):
    #     redirect_url = "http://example.com/"
    #     state = AuthenticationService.generate_state(redirect_url)
    #     with current_app.app_context():
    #         login_redirect_url = AuthenticationService().get_login_redirect_url(state.decode("UTF-8"))
    #         print("test_get_login_redirect_url")
    #     print("test_get_login_redirect_url")

    # def test_get_token_script(self, app: Flask) -> None:
    #     """Test_get_token_script."""
    #     print("Test Get Token Script")
    #
    #     (
    #         keycloak_server_url,
    #         keycloak_client_id,
    #         keycloak_realm_name,
    #         keycloak_client_secret_key,
    #     ) = self.get_keycloak_constants(app)
    #     keycloak_user = "ciuser1"
    #     keycloak_pass = "ciuser1"  # noqa: S105
    #
    #     print(f"Test Get Token Script: keycloak_server_url: {keycloak_server_url}")
    #     print(f"Test Get Token Script: keycloak_client_id: {keycloak_client_id}")
    #     print(f"Test Get Token Script: keycloak_realm_name: {keycloak_realm_name}")
    #     print(
    #         f"Test Get Token Script: keycloak_client_secret_key: {keycloak_client_secret_key}"
    #     )
    #
    #     frontend_client_id = "spiffworkflow-frontend"
    #
    #     print(f"Test Get Token Script: frontend_client_id: {frontend_client_id}")
    #
    #     # Get frontend token
    #     request_url = f"{keycloak_server_url}/realms/{keycloak_realm_name}/protocol/openid-connect/token"
    #     headers = {"Content-Type": "application/x-www-form-urlencoded"}
    #     post_data = {
    #         "grant_type": "password",
    #         "username": keycloak_user,
    #         "password": keycloak_pass,
    #         "client_id": frontend_client_id,
    #     }
    #     print(f"Test Get Token Script: request_url: {request_url}")
    #     print(f"Test Get Token Script: headers: {headers}")
    #     print(f"Test Get Token Script: post_data: {post_data}")
    #
    #     frontend_response = requests.post(
    #         request_url, headers=headers, json=post_data, data=post_data
    #     )
    #     frontend_token = json.loads(frontend_response.text)
    #
    #     print(f"Test Get Token Script: frontend_response: {frontend_response}")
    #     print(f"Test Get Token Script: frontend_token: {frontend_token}")
    #
    #     # assert isinstance(frontend_token, dict)
    #     # assert isinstance(frontend_token["access_token"], str)
    #     # assert isinstance(frontend_token["refresh_token"], str)
    #     # assert frontend_token["expires_in"] == 300
    #     # assert frontend_token["refresh_expires_in"] == 1800
    #     # assert frontend_token["token_type"] == "Bearer"
    #
    #     # Get backend token
    #     backend_basic_auth_string = f"{keycloak_client_id}:{keycloak_client_secret_key}"
    #     backend_basic_auth_bytes = bytes(backend_basic_auth_string, encoding="ascii")
    #     backend_basic_auth = base64.b64encode(backend_basic_auth_bytes)
    #
    #     request_url = f"{keycloak_server_url}/realms/{keycloak_realm_name}/protocol/openid-connect/token"
    #     headers = {
    #         "Content-Type": "application/x-www-form-urlencoded",
    #         "Authorization": f"Basic {backend_basic_auth.decode('utf-8')}",
    #     }
    #     data = {
    #         "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
    #         "client_id": keycloak_client_id,
    #         "subject_token": frontend_token["access_token"],
    #         "audience": keycloak_client_id,
    #     }
    #     print(f"Test Get Token Script: request_url: {request_url}")
    #     print(f"Test Get Token Script: headers: {headers}")
    #     print(f"Test Get Token Script: data: {data}")
    #
    #     backend_response = requests.post(request_url, headers=headers, data=data)
    #     json_data = json.loads(backend_response.text)
    #     backend_token = json_data["access_token"]
    #     print(f"Test Get Token Script: backend_response: {backend_response}")
    #     print(f"Test Get Token Script: backend_token: {backend_token}")
    #
    #     if backend_token:
    #         # Getting resource set
    #         auth_bearer_string = f"Bearer {backend_token}"
    #         headers = {
    #             "Content-Type": "application/json",
    #             "Authorization": auth_bearer_string,
    #         }
    #
    #         # uri_to_test_against = "%2Fprocess-models"
    #         uri_to_test_against = "/status"
    #         request_url = (
    #             f"{keycloak_server_url}/realms/{keycloak_realm_name}/authz/protection/resource_set?"
    #             + f"matchingUri=true&deep=true&max=-1&exactName=false&uri={uri_to_test_against}"
    #         )
    #         # f"uri={uri_to_test_against}"
    #         print(f"Test Get Token Script: request_url: {request_url}")
    #         print(f"Test Get Token Script: headers: {headers}")
    #
    #         resource_result = requests.get(request_url, headers=headers)
    #         print(f"Test Get Token Script: resource_result: {resource_result}")
    #
    #         json_data = json.loads(resource_result.text)
    #         resource_id_name_pairs = []
    #         for result in json_data:
    #             if "_id" in result and result["_id"]:
    #                 pair_key = result["_id"]
    #                 if "name" in result and result["name"]:
    #                     pair_value = result["name"]
    #                     # pair = {{result['_id']}: {}}
    #                 else:
    #                     pair_value = "no_name"
    #                     # pair = {{result['_id']}: }
    #                 pair = [pair_key, pair_value]
    #                 resource_id_name_pairs.append(pair)
    #         print(
    #             f"Test Get Token Script: resource_id_name_pairs: {resource_id_name_pairs}"
    #         )
    #
    #         # Getting Permissions
    #         for resource_id_name_pair in resource_id_name_pairs:
    #             resource_id = resource_id_name_pair[0]
    #             resource_id_name_pair[1]
    #
    #             headers = {
    #                 "Content-Type": "application/x-www-form-urlencoded",
    #                 "Authorization": f"Basic {backend_basic_auth.decode('utf-8')}",
    #             }
    #
    #             post_data = {
    #                 "audience": keycloak_client_id,
    #                 "permission": resource_id,
    #                 "subject_token": backend_token,
    #                 "grant_type": "urn:ietf:params:oauth:grant-type:uma-ticket",
    #             }
    #             print(f"Test Get Token Script: headers: {headers}")
    #             print(f"Test Get Token Script: post_data: {post_data}")
    #             print(f"Test Get Token Script: request_url: {request_url}")
    #
    #             permission_result = requests.post(
    #                 request_url, headers=headers, data=post_data
    #             )
    #             print(f"Test Get Token Script: permission_result: {permission_result}")
    #
    #     print("test_get_token_script")
