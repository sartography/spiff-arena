import ast
import base64
import re
import time
import urllib.parse

import pytest
from flask.app import Flask
from pytest_mock.plugin import MockerFixture
from starlette.testclient import TestClient

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.pkce_code_verifier import PkceCodeVerifierModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.authentication_service import PKCE
from spiffworkflow_backend.services.authentication_service import AuthenticationService
from spiffworkflow_backend.services.authorization_service import AuthorizationService
from spiffworkflow_backend.services.authorization_service import GroupPermissionsDict
from spiffworkflow_backend.services.service_account_service import ServiceAccountService
from spiffworkflow_backend.services.user_service import UserService
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestAuthentication(BaseTest):
    def test_get_login_state_without_pkce_enabled(self, app: Flask) -> None:
        with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_OPEN_ID_ENFORCE_PKCE", False):
            redirect_url = "http://example.com/"
            state_payload = AuthenticationService.generate_state_payload(
                authentication_identifier="default", final_url=redirect_url
            )
            state = AuthenticationService.encode_state_payload(state_payload)
            state_dict = ast.literal_eval(base64.b64decode(state).decode("UTF-8"))

            assert isinstance(state_dict, dict)
            assert state_dict["final_url"] == redirect_url

    def test_get_login_state_with_pkce_enabled(self, app: Flask) -> None:
        with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_OPEN_ID_ENFORCE_PKCE", True):
            redirect_url = "http://example.com/"
            state_payload = AuthenticationService.generate_state_payload(
                authentication_identifier="default", final_url=redirect_url
            )
            state = AuthenticationService.encode_state_payload(state_payload)
            state_dict = ast.literal_eval(base64.b64decode(state).decode("UTF-8"))

            assert isinstance(state_dict, dict)
            assert isinstance(state_dict["pkce_id"], str)

    def test_properly_adds_user_to_groups_from_token_on_login(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_OPEN_ID_IS_AUTHORITY_FOR_USER_GROUPS", True):
            group_one = UserService.find_or_create_group("group_one")
            assert group_one.source_is_open_id is False

            user = self.find_or_create_user("testing@example.com")
            user.email = "testing@example.com"
            user.service = app.config["SPIFFWORKFLOW_BACKEND_AUTH_CONFIGS"][0]["uri"]
            user.service_id = f"service:{user.service}::service_id:{user.service_id}"
            db.session.add(user)
            db.session.commit()

            access_token = user.encode_auth_token(
                {
                    "groups": ["group_one", "group_two"],
                    "iss": user.service,
                    "sub": user.service_id,
                    "aud": "spiffworkflow-backend",
                }
            )
            response = None
            response = client.post(
                f"/v1.0/login_with_access_token?access_token={access_token}&authentication_identifier=default",
            )
            assert response.status_code == 200
            assert len(user.groups) == 3
            group_identifiers = [g.identifier for g in user.groups]
            assert sorted(group_identifiers) == ["everybody", "group_one", "group_two"]
            open_id_array = [g.source_is_open_id for g in user.groups if g.identifier in ["group_one", "group_two"]]
            assert open_id_array == [True, True]
            everybody_is_open_id = next((g.source_is_open_id for g in user.groups if g.identifier == "everybody"), None)
            assert everybody_is_open_id is False

            access_token = user.encode_auth_token(
                {
                    "groups": ["group_one"],
                    "iss": user.service,
                    "sub": user.service_id,
                    "aud": "spiffworkflow-backend",
                }
            )
            response = client.post(
                f"/v1.0/login_with_access_token?access_token={access_token}&authentication_identifier=default",
            )
            assert response.status_code == 200
            user = UserModel.query.filter_by(username=user.username).first()
            assert len(user.groups) == 2
            group_identifiers = [g.identifier for g in user.groups]
            assert sorted(group_identifiers) == ["everybody", "group_one"]

            # make sure running refresh_permissions doesn't remove the user from the group
            group_info: list[GroupPermissionsDict] = [
                {
                    "users": [],
                    "name": "group_one",
                    "permissions": [{"actions": ["create", "read"], "uri": "PG:hey"}],
                }
            ]
            AuthorizationService.refresh_permissions(group_info, group_permissions_only=True)
            user = UserModel.query.filter_by(username=user.username).first()
            assert len(user.groups) == 2
            group_identifiers = [g.identifier for g in user.groups]
            assert sorted(group_identifiers) == ["everybody", "group_one"]
            self.assert_user_has_permission(user, "read", "/v1.0/process-groups/hey")
            self.assert_user_has_permission(user, "read", "/v1.0/process-groups/hey:yo")

    def test_does_not_remove_permissions_from_service_accounts_on_refresh(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        service_account = ServiceAccountService.create_service_account("sa_api_key", with_super_admin_user)
        service_account_permissions_before = sorted(
            UserService.get_permission_targets_for_user(service_account.user, check_groups=False)
        )

        # make sure running refresh_permissions doesn't remove the user from the group
        group_info: list[GroupPermissionsDict] = [
            {
                "users": [],
                "name": "group_one",
                "permissions": [{"actions": ["create", "read"], "uri": "PG:hey"}],
            }
        ]
        AuthorizationService.refresh_permissions(group_info, group_permissions_only=True)

        service_account_permissions_after = sorted(
            UserService.get_permission_targets_for_user(service_account.user, check_groups=False)
        )
        assert service_account_permissions_before == service_account_permissions_after

    def test_can_login_with_valid_user(
        self,
        app: Flask,
        mocker: MockerFixture,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        redirect_uri = f"{app.config['SPIFFWORKFLOW_BACKEND_URL_FOR_FRONTEND']}/test-redirect-dne"
        auth_uri = app.config["SPIFFWORKFLOW_BACKEND_AUTH_CONFIGS"][0]["uri"]
        login_return_uri = f"{app.config['SPIFFWORKFLOW_BACKEND_URL']}/v1.0/login_return"

        class_method_mock = mocker.patch(
            "spiffworkflow_backend.services.authentication_service.AuthenticationService.open_id_endpoint_for_name",
            return_value=auth_uri,
        )

        response = client.get(
            f"/v1.0/login?redirect_url={redirect_uri}&authentication_identifier=default",
        )

        assert class_method_mock.call_count == 1
        assert response.status_code == 302
        assert response.has_redirect_location
        redirect_location = response.headers["location"]
        assert redirect_location.startswith(auth_uri)
        assert re.search(r"\bredirect_uri=" + re.escape(login_return_uri), redirect_location) is not None

    def test_raises_error_if_invalid_redirect_url(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        redirect_url = "http://www.bad_url.com/test-redirect-dne"
        response = client.get(
            f"/v1.0/login?redirect_url={redirect_url}&authentication_identifier=DOES_NOT_MATTER",
        )
        assert response.status_code == 500
        assert response.json() is not None
        assert response.json()["message"].startswith("InvalidRedirectUrlError:")

    def test_can_access_public_endpoints_and_get_token(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        group_info: list[GroupPermissionsDict] = [
            {
                "users": [],
                "name": app.config["SPIFFWORKFLOW_BACKEND_DEFAULT_PUBLIC_USER_GROUP"],
                "permissions": [{"actions": ["create", "read"], "uri": "/public/*"}],
            }
        ]
        AuthorizationService.refresh_permissions(group_info, group_permissions_only=True)
        process_model = load_test_spec(
            process_model_id="test_group/message-start-event-with-form",
            process_model_source_directory="message-start-event-with-form",
        )
        process_group_identifier, _ = process_model.modified_process_model_identifier().rsplit(":", 1)
        url = f"/v1.0/public/messages/form/{process_group_identifier}:bounty_start"

        response = client.get(url)
        assert response.status_code == 200
        assert "Set-Cookie" in response.headers
        cookie = response.headers["Set-Cookie"]
        cookie_split = cookie.split(";")
        access_token = [cookie for cookie in cookie_split if cookie.startswith("access_token=")][0]
        assert access_token is not None
        re_result = re.match(r"^access_token=[\w_\.-]+$", access_token)
        assert re_result is not None

        response = client.get(
            url,
            headers={"Authorization": "Bearer " + access_token.split("=")[1]},
        )
        assert response.status_code == 200

        # make sure we do not create and set a new cookie with this request
        assert "Set-Cookie" not in response.headers

        response = client.get(
            "/v1.0/process-groups",
            headers={"Authorization": "Bearer " + access_token.split("=")[1]},
        )
        assert response.status_code == 403

    def test_login_return_with_error(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        """Test that the login_return endpoint handles errors from the OIDC provider."""
        error = "access_denied"
        error_description = "User is not assigned to the client application."
        state_payload = AuthenticationService.generate_state_payload(authentication_identifier="default", final_url="/")
        state = AuthenticationService.encode_state_payload(state_payload)
        url = f"/v1.0/login_return?state={state.decode()}&error={error}&error_description={error_description}"

        response = client.get(url)

        assert response.status_code == 401
        response_text = response.text
        assert "<h1>Authentication Error</h1>" in response_text
        assert f"<strong>Error:</strong> {error}" in response_text
        assert f"<strong>Description:</strong> {error_description}" in response_text

    def test_login_return_contains_pkce_parameters_when_pkce_enforced(
        self,
        app: Flask,
        mocker: MockerFixture,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_OPEN_ID_ENFORCE_PKCE", True):
            redirect_uri = f"{app.config['SPIFFWORKFLOW_BACKEND_URL_FOR_FRONTEND']}/test-redirect-dne"
            auth_uri = app.config["SPIFFWORKFLOW_BACKEND_AUTH_CONFIGS"][0]["uri"]

            mocker.patch(
                "spiffworkflow_backend.services.authentication_service.AuthenticationService.open_id_endpoint_for_name",
                return_value=auth_uri,
            )

            response = client.get(
                f"/v1.0/login?redirect_url={redirect_uri}&authentication_identifier=default", follow_redirects=True
            )
            parsed_url = urllib.parse.urlparse(str(response.url))
            params = urllib.parse.parse_qs(parsed_url.query)
            state = params.get("state", [])[0]
            state_dict = ast.literal_eval(base64.b64decode(state).decode("utf-8"))

            assert params.get(PKCE.CODE_CHALLENGE_KEY, [])[0]
            assert params.get(PKCE.CODE_CHALLENGE_METHOD_KEY, [])[0] == "S256"
            assert isinstance(state_dict["pkce_id"], str)

    def test_get_auth_token_throws_errors_for_misconfigured_pkce(self, app: Flask, mocker: MockerFixture) -> None:
        # Mock the redirect URI method since we're testing PKCE validation, not URL building.
        # There's some bad interaction with another test depnding on test order.
        # Not sure if it's about connexion and url building, etc.
        mocker.patch(
            "spiffworkflow_backend.services.authentication_service.AuthenticationService.get_redirect_uri_for_login_to_server",
            return_value="https://example.com/v1.0/login_return",
        )

        with app.test_request_context(
            "/some/path",
            base_url="https://example.com/",  # this is what request.host_url will be based on
        ):
            with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_OPEN_ID_ENFORCE_PKCE", True):
                with pytest.raises(
                    ApiError,
                    match="PKCE is enforced but PKCE identifier is missing from state",
                ):
                    AuthenticationService().get_auth_token_object(code="fake_auth_code", authentication_identifier="default")
                with pytest.raises(
                    ApiError,
                    match="ApiError: PKCE is enforced but code verifier is missing from storage",
                ):
                    AuthenticationService().get_auth_token_object(
                        code="fake_auth_code", authentication_identifier="default", pkce_id="invalid_pkce_id"
                    )

    def test_delete_expired_pkce_verifiers(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        max_pkce_verifier_time_in_seconds = 100

        non_expired = PkceCodeVerifierModel(pkce_id="1", code_verifier="test_verifier_1")
        expired = PkceCodeVerifierModel(pkce_id="2", code_verifier="test_verifier_2")

        db.session.add_all([non_expired, expired])
        db.session.commit()

        # On creation, SpiffworkflowBaseDBModel automatically sets created_at_in_seconds to "now."
        # We override the timestamps to control expiry behavior explicitly.
        now = round(time.time())
        expired.created_at_in_seconds = now - max_pkce_verifier_time_in_seconds
        non_expired.created_at_in_seconds = now - max_pkce_verifier_time_in_seconds + 1
        db.session.commit()

        assert PkceCodeVerifierModel.query.count() == 2

        deleted_count = PKCE.delete_expired_pkce_code_verifiers(max_pkce_verifier_time_in_seconds)
        assert deleted_count == 1

        remaining = PkceCodeVerifierModel.query.all()
        assert len(remaining) == 1
        assert remaining[0].pkce_id == non_expired.pkce_id
