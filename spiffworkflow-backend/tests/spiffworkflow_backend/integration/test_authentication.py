import ast
import base64
import re
import time
import urllib.parse
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from flask.app import Flask
from pytest_mock.plugin import MockerFixture
from starlette.testclient import TestClient
from werkzeug.wrappers import Response as WerkzeugResponse

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.exceptions.error import TokenExpiredError
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.pkce_code_verifier import PkceCodeVerifierModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.routes.authentication_controller import _clear_auth_tokens_from_thread_local_data
from spiffworkflow_backend.routes.authentication_controller import _get_user_model_from_token
from spiffworkflow_backend.routes.service_tasks_controller import authentication_begin
from spiffworkflow_backend.routes.service_tasks_controller import authentication_list
from spiffworkflow_backend.services.authentication_service import PKCE
from spiffworkflow_backend.services.authentication_service import AuthenticationService
from spiffworkflow_backend.services.authorization_service import AuthorizationService
from spiffworkflow_backend.services.authorization_service import GroupPermissionsDict
from spiffworkflow_backend.services.service_account_service import ServiceAccountService
from spiffworkflow_backend.services.user_service import UserService
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestAuthentication(BaseTest):
    def test_authentication_list_redirect_url_uses_public_backend_base(
        self,
        app: Flask,
        mocker: MockerFixture,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        with (
            self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_URL", "https://backend.example.com/api"),
            self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_API_PATH_PREFIX", "/api/v1.0"),
        ):
            with app.test_request_context("/v1.0/authentications"):
                mocker.patch(
                    "spiffworkflow_backend.routes.service_tasks_controller.ServiceTaskService.authentication_list",
                    return_value=[],
                )
                mocker.patch(
                    "spiffworkflow_backend.routes.service_tasks_controller.OAuthService.authentication_list",
                    return_value=[],
                )
                response = authentication_list()

        assert response.status_code == 200
        assert response.get_json()["redirect_url"] == "https://backend.example.com/api/v1.0/authentication_callback"

    def test_authentication_begin_callback_uses_public_backend_base(
        self,
        app: Flask,
        mocker: MockerFixture,
    ) -> None:
        remote_app = MagicMock()
        redirect_response = WerkzeugResponse(status=302)
        remote_app.authorize.return_value = redirect_response

        with (
            self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_URL", "https://backend.example.com/api"),
            self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_API_PATH_PREFIX", "/api/v1.0"),
        ):
            with app.test_request_context("/v1.0/authentication_begin/example/oauth?token=test-token"):
                mocker.patch("spiffworkflow_backend.routes.service_tasks_controller.verify_token", return_value=None)
                mocker.patch(
                    "spiffworkflow_backend.routes.service_tasks_controller.OAuthService.supported_service",
                    return_value=True,
                )
                mocker.patch(
                    "spiffworkflow_backend.routes.service_tasks_controller.OAuthService.remote_app",
                    return_value=remote_app,
                )
                response = authentication_begin("example", "oauth")

        assert response is redirect_response
        remote_app.authorize.assert_called_once_with(
            callback="https://backend.example.com/api/v1.0/authentication_callback/example/oauth",
            _external=True,
        )

    def test_logout_redirect_url_uses_public_backend_base(self, app: Flask) -> None:
        with (
            self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_URL", "https://backend.example.com/api"),
            self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_API_PATH_PREFIX", "/api/v1.0"),
        ):
            with app.test_request_context():
                with patch.object(
                    AuthenticationService,
                    "open_id_endpoint_for_name",
                    return_value="https://auth.example.com/logout",
                ):
                    response = AuthenticationService().logout("test-id-token", "default")

        assert response.location == (
            "https://auth.example.com/logout"
            "?post_logout_redirect_uri=https%3A%2F%2Fbackend.example.com%2Fapi%2Fv1.0%2Flogout_return&"
            "id_token_hint=test-id-token"
        )

    def test_logout_request_can_be_configured_per_authentication_provider(self, app: Flask) -> None:
        authentication_options = [
            app.config["SPIFFWORKFLOW_BACKEND_AUTH_CONFIGS"][0],
            {
                **app.config["SPIFFWORKFLOW_BACKEND_AUTH_CONFIGS"][0],
                "identifier": "provider-with-custom-logout",
                "client_id": "custom-client-id",
                "logout_redirect_uri_parameter": "return_to",
                "logout_include_client_id": "true",
                "logout_include_id_token_hint": "false",
            },
        ]
        with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_AUTH_CONFIGS", authentication_options):
            with app.test_request_context():
                with patch.object(
                    AuthenticationService,
                    "open_id_endpoint_for_name",
                    return_value="https://auth.example.com/logout?existing=value",
                ):
                    response = AuthenticationService().logout(
                        "test-id-token",
                        "provider-with-custom-logout",
                        "https://arena.example.com/signed-out?from=logout",
                    )

        assert response.location == (
            "https://auth.example.com/logout?existing=value&client_id=custom-client-id&"
            "return_to=https%3A%2F%2Farena.example.com%2Fsigned-out%3Ffrom%3Dlogout"
        )

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
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # This test covers group preservation during refresh, not the contents of
        # the application's full permissions file.
        monkeypatch.setattr(AuthorizationService, "load_permissions_yaml", lambda: {})
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
                "/v1.0/login_with_access_token?authentication_identifier=default",
                headers={"Authorization": f"Bearer {access_token}"},
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
                "/v1.0/login_with_access_token?authentication_identifier=default",
                headers={"Authorization": f"Bearer {access_token}"},
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

    def test_login_with_access_token_accepts_bearer_token(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        user = self.find_or_create_user("testing@example.com")
        user.email = "testing@example.com"
        user.service = app.config["SPIFFWORKFLOW_BACKEND_AUTH_CONFIGS"][0]["uri"]
        user.service_id = f"service:{user.service}::service_id:{user.service_id}"
        db.session.add(user)
        db.session.commit()

        access_token = user.encode_auth_token(
            {
                "iss": user.service,
                "sub": user.service_id,
                "aud": "spiffworkflow-backend",
            }
        )
        response = client.post(
            "/v1.0/login_with_access_token?authentication_identifier=default",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200

    def test_login_with_access_token_adopts_existing_user_with_matching_email(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        user = UserService.create_user("samwise", "local_open_id", "samwise", email="samwise@example.com")
        access_token = user.encode_auth_token(
            {
                "iss": app.config["SPIFFWORKFLOW_BACKEND_AUTH_CONFIGS"][0]["uri"],
                "sub": "keycloak-samwise",
                "aud": "spiffworkflow-backend",
                "preferred_username": "samwise",
                "email": "samwise@example.com",
            }
        )

        response = client.post(
            "/v1.0/login_with_access_token?authentication_identifier=default",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        user = UserModel.query.filter_by(username="samwise").one()
        assert user.email == "samwise@example.com"
        assert user.service == app.config["SPIFFWORKFLOW_BACKEND_AUTH_CONFIGS"][0]["uri"]
        assert user.service_id == "keycloak-samwise"

    def test_login_with_access_token_adopts_first_existing_user_with_matching_email(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        older_user = UserService.create_user("older_duplicate", "local_open_id", "older", email="duplicate@example.com")
        newer_user = UserService.create_user("newer_duplicate", "local_open_id", "newer", email="duplicate@example.com")
        older_user_id = older_user.id
        newer_user_id = newer_user.id
        access_token = older_user.encode_auth_token(
            {
                "iss": app.config["SPIFFWORKFLOW_BACKEND_AUTH_CONFIGS"][0]["uri"],
                "sub": "keycloak-duplicate",
                "aud": "spiffworkflow-backend",
                "preferred_username": "duplicate-login",
                "email": "duplicate@example.com",
            }
        )

        response = client.post(
            "/v1.0/login_with_access_token?authentication_identifier=default",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        adopted_user = UserModel.query.filter_by(username="duplicate-login").one()
        assert adopted_user.id == older_user_id
        assert adopted_user.service == app.config["SPIFFWORKFLOW_BACKEND_AUTH_CONFIGS"][0]["uri"]
        assert adopted_user.service_id == "keycloak-duplicate"
        assert UserModel.query.filter_by(id=newer_user_id).one().username == "newer_duplicate"

    def test_legacy_access_token_audiences_remain_backward_compatible(self, app: Flask) -> None:
        auth_configs = [
            {
                **app.config["SPIFFWORKFLOW_BACKEND_AUTH_CONFIGS"][0],
                "additional_valid_client_ids": "spiffworks-ed, other-client",
            }
        ]
        now = round(time.time())
        with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_AUTH_CONFIGS", auth_configs):
            assert AuthenticationService.valid_audiences("default") == [
                auth_configs[0]["client_id"],
                "spiffworks-ed",
                "other-client",
                "account",
            ]
            assert AuthenticationService.validate_decoded_access_token(
                {
                    "iss": auth_configs[0]["uri"],
                    "sub": "samwise",
                    "aud": "spiffworks-ed",
                    "azp": "spiffworks-ed",
                    "iat": now,
                    "exp": now + 60,
                },
                "default",
            )

    def test_id_and_access_tokens_use_separate_audiences(self, app: Flask) -> None:
        api_audience = "https://arena.example.com/api"
        auth_config = {
            **app.config["SPIFFWORKFLOW_BACKEND_AUTH_CONFIGS"][0],
            "access_token_audiences": [api_audience],
            "authorization_resource": api_audience,
        }
        now = round(time.time())
        with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_AUTH_CONFIGS", [auth_config]):
            assert AuthenticationService.validate_decoded_id_token(
                {
                    "iss": auth_config["uri"],
                    "sub": "samwise",
                    "aud": auth_config["client_id"],
                    "token_use": "id",
                    "iat": now,
                    "exp": now + 60,
                },
                "default",
            )
            assert AuthenticationService.validate_decoded_access_token(
                {
                    "iss": auth_config["uri"],
                    "sub": "samwise",
                    "aud": api_audience,
                    "client_id": auth_config["client_id"],
                    "token_use": "access",
                    "iat": now,
                    "exp": now + 60,
                },
                "default",
            )

    @pytest.mark.parametrize(
        "provider_client_claim",
        ["azp", "cid"],
        ids=["keycloak", "okta"],
    )
    def test_explicit_access_token_audience_supports_provider_client_claims(
        self,
        app: Flask,
        provider_client_claim: str,
    ) -> None:
        api_audience = "https://arena.example.com/api"
        auth_config = {
            **app.config["SPIFFWORKFLOW_BACKEND_AUTH_CONFIGS"][0],
            "access_token_audiences": api_audience,
        }
        now = round(time.time())
        decoded_token = {
            "iss": auth_config["uri"],
            "sub": "samwise",
            "aud": api_audience,
            provider_client_claim: auth_config["client_id"],
            "iat": now,
            "exp": now + 60,
        }
        with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_AUTH_CONFIGS", [auth_config]):
            assert AuthenticationService.validate_decoded_access_token(decoded_token, "default")

    def test_explicit_access_token_audience_rejects_wrong_token_type_and_client(self, app: Flask) -> None:
        api_audience = "https://arena.example.com/api"
        auth_config = {
            **app.config["SPIFFWORKFLOW_BACKEND_AUTH_CONFIGS"][0],
            "access_token_audiences": [api_audience],
        }
        now = round(time.time())
        common_claims = {
            "iss": auth_config["uri"],
            "sub": "samwise",
            "aud": api_audience,
            "iat": now,
            "exp": now + 60,
        }
        with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_AUTH_CONFIGS", [auth_config]):
            assert not AuthenticationService.validate_decoded_access_token(
                {**common_claims, "client_id": auth_config["client_id"], "token_use": "id"},
                "default",
            )
            assert not AuthenticationService.validate_decoded_access_token(
                {**common_claims, "cid": "different-client"},
                "default",
            )

    def test_token_validation_failure_records_low_cardinality_metric(
        self,
        app: Flask,
        mocker: MockerFixture,
    ) -> None:
        counter = mocker.patch("spiffworkflow_backend.services.authentication_service.TOKEN_VALIDATION_FAILURES")
        now = round(time.time())
        with app.app_context():
            valid = AuthenticationService.validate_decoded_token(
                {
                    "iss": "https://untrusted.example",
                    "sub": "samwise",
                    "aud": AuthenticationService.client_id("default"),
                    "azp": AuthenticationService.client_id("default"),
                    "iat": now,
                    "exp": now + 60,
                },
                "default",
            )

        assert valid is False
        counter.labels.assert_called_once_with(reason="issuer")
        counter.labels.return_value.inc.assert_called_once_with()

    def test_does_not_remove_permissions_from_service_accounts_on_refresh(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # Keep refresh real while limiting its unrelated YAML input.
        monkeypatch.setattr(AuthorizationService, "load_permissions_yaml", lambda: {})
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

    def test_login_redirect_includes_configured_authorization_resource(
        self,
        app: Flask,
        mocker: MockerFixture,
        client: TestClient,
    ) -> None:
        api_audience = "https://arena.example.com/api"
        auth_uri = app.config["SPIFFWORKFLOW_BACKEND_AUTH_CONFIGS"][0]["uri"]
        auth_config = {
            **app.config["SPIFFWORKFLOW_BACKEND_AUTH_CONFIGS"][0],
            "authorization_resource": api_audience,
        }
        mocker.patch.object(AuthenticationService, "open_id_endpoint_for_name", return_value=auth_uri)

        with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_AUTH_CONFIGS", [auth_config]):
            response = client.get(
                "/v1.0/login",
                params={
                    "redirect_url": f"{app.config['SPIFFWORKFLOW_BACKEND_URL_FOR_FRONTEND']}/after-login",
                    "authentication_identifier": "default",
                },
            )

        assert response.status_code == 302
        params = urllib.parse.parse_qs(urllib.parse.urlparse(response.headers["location"]).query)
        assert params["resource"] == [api_audience]

    def test_login_return_uses_access_token_for_api_cookie(
        self,
        app: Flask,
        mocker: MockerFixture,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        auth_config = app.config["SPIFFWORKFLOW_BACKEND_AUTH_CONFIGS"][0]
        user = self.find_or_create_user("access-token-cookie-user@example.com")
        id_token = user.encode_auth_token(
            {
                "iss": auth_config["uri"],
                "sub": "access-token-cookie-user",
                "aud": auth_config["client_id"],
                "preferred_username": "access-token-cookie-user",
                "email": "access-token-cookie-user@example.com",
            }
        )
        access_token = "provider-access-token"  # noqa: S105 -- deliberately distinct from the ID token
        store_refresh_token = mocker.patch.object(AuthenticationService, "store_refresh_token")
        mocker.patch.object(
            AuthenticationService,
            "get_auth_token_object",
            return_value={
                "access_token": access_token,
                "id_token": id_token,
                "refresh_token": "provider-refresh-token",
            },
        )
        redirect_url = f"{app.config['SPIFFWORKFLOW_BACKEND_URL_FOR_FRONTEND']}/after-login"
        state_payload = AuthenticationService.generate_state_payload(authentication_identifier="default", final_url=redirect_url)
        state = AuthenticationService.encode_state_payload(state_payload)

        response = client.get(
            "/v1.0/login_return",
            params={"state": state.decode(), "code": "provider-authorization-code"},
        )

        assert response.status_code == 302
        assert response.headers["location"] == redirect_url
        assert response.cookies["access_token"] == access_token
        assert response.cookies["id_token"] == id_token
        store_refresh_token.assert_called_once()

    def test_refresh_uses_refreshed_access_token_for_api_cookie(
        self,
        app: Flask,
        mocker: MockerFixture,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        auth_config = app.config["SPIFFWORKFLOW_BACKEND_AUTH_CONFIGS"][0]
        user = self.find_or_create_user("refreshed-access-token-user@example.com")
        user.service = auth_config["uri"]
        user.service_id = "refreshed-access-token-user"
        db.session.add(user)
        db.session.commit()
        mocker.patch.object(
            AuthenticationService,
            "validate_decoded_access_token",
            side_effect=TokenExpiredError("expired"),
        )
        mocker.patch.object(AuthenticationService, "get_refresh_token", return_value="stored-refresh-token")
        mocker.patch.object(
            AuthenticationService,
            "get_auth_token_from_refresh_token",
            return_value={
                "access_token": "refreshed-provider-access-token",
                "id_token": "refreshed-provider-id-token",
                "refresh_token": "rotated-provider-refresh-token",
            },
        )
        store_refresh_token = mocker.patch.object(AuthenticationService, "store_refresh_token")

        with app.test_request_context(
            "/v1.0/status",
            headers={"SpiffWorkflow-Authentication-Identifier": "default"},
        ):
            try:
                refreshed_user = _get_user_model_from_token(
                    {
                        "iss": auth_config["uri"],
                        "sub": user.service_id,
                    }
                )
                tld = app.config["THREAD_LOCAL_DATA"]

                assert refreshed_user == user
                assert tld.new_access_token == "refreshed-provider-access-token"  # noqa: S105
                assert tld.new_id_token == "refreshed-provider-id-token"  # noqa: S105
                store_refresh_token.assert_called_once_with(user.id, "rotated-provider-refresh-token")
            finally:
                _clear_auth_tokens_from_thread_local_data()

    def test_can_login_with_local_development_frontend_hostname_alias(
        self,
        app: Flask,
        mocker: MockerFixture,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        redirect_uri = "http://spiff-dev-host:7001/test-redirect-dne"
        auth_uri = app.config["SPIFFWORKFLOW_BACKEND_AUTH_CONFIGS"][0]["uri"]

        class_method_mock = mocker.patch(
            "spiffworkflow_backend.services.authentication_service.AuthenticationService.open_id_endpoint_for_name",
            return_value=auth_uri,
        )

        with (
            self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_URL_FOR_FRONTEND", "http://localhost:7001"),
            self.app_config_mock(
                app,
                "SPIFFWORKFLOW_BACKEND_ALLOWED_REDIRECT_HOST_ALIASES",
                "localhost,spiff-dev-host",
            ),
        ):
            response = client.get(
                f"/v1.0/login?redirect_url={redirect_uri}&authentication_identifier=default",
            )

        assert class_method_mock.call_count == 1
        assert response.status_code == 302
        assert response.has_redirect_location
        assert response.headers["location"].startswith(auth_uri)

    def test_rejects_unconfigured_local_development_frontend_hostname_alias(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        redirect_uri = "http://unconfigured-dev-host:7001/test-redirect-dne"

        response = client.get(
            f"/v1.0/login?redirect_url={redirect_uri}&authentication_identifier=DOES_NOT_MATTER",
        )

        assert response.status_code == 500
        assert response.json() is not None
        assert response.json()["message"].startswith("InvalidRedirectUrlError:")

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

    def test_raises_error_if_redirect_url_only_has_frontend_url_as_host_prefix(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        redirect_url = f"{app.config['SPIFFWORKFLOW_BACKEND_URL_FOR_FRONTEND']}.bad_url.com/test-redirect-dne"
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
        AuthorizationService.add_permissions_from_group_permissions(group_info, group_permissions_only=True)
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

    def test_local_development_frontend_hostname_uses_host_only_cookie(
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
        AuthorizationService.add_permissions_from_group_permissions(group_info, group_permissions_only=True)
        process_model = load_test_spec(
            process_model_id="test_group/message-start-event-with-form",
            process_model_source_directory="message-start-event-with-form",
        )
        process_group_identifier, _ = process_model.modified_process_model_identifier().rsplit(":", 1)

        with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_URL_FOR_FRONTEND", "http://spiff-dev-host:7001"):
            response = client.get(f"/v1.0/public/messages/form/{process_group_identifier}:bounty_start")

        assert response.status_code == 200
        assert "Set-Cookie" in response.headers
        assert "Domain=" not in response.headers["Set-Cookie"]

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
        expired.created_at_in_seconds = now - max_pkce_verifier_time_in_seconds - 5
        non_expired.created_at_in_seconds = now - max_pkce_verifier_time_in_seconds + 5
        db.session.commit()

        assert PkceCodeVerifierModel.query.count() == 2

        deleted_count = PKCE.delete_expired_pkce_code_verifiers(max_pkce_verifier_time_in_seconds)
        assert deleted_count == 1

        remaining = PkceCodeVerifierModel.query.all()
        assert len(remaining) == 1
        assert remaining[0].pkce_id == non_expired.pkce_id
