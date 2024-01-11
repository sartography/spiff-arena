import ast
import base64
import re

from flask.app import Flask
from flask.testing import FlaskClient
from pytest_mock.plugin import MockerFixture
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.authentication_service import AuthenticationService
from spiffworkflow_backend.services.authorization_service import AuthorizationService
from spiffworkflow_backend.services.authorization_service import GroupPermissionsDict
from spiffworkflow_backend.services.service_account_service import ServiceAccountService
from spiffworkflow_backend.services.user_service import UserService

from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestAuthentication(BaseTest):
    def test_get_login_state(self) -> None:
        redirect_url = "http://example.com/"
        state = AuthenticationService.generate_state(redirect_url, authentication_identifier="default")
        state_dict = ast.literal_eval(base64.b64decode(state).decode("utf-8"))

        assert isinstance(state_dict, dict)
        assert "redirect_url" in state_dict.keys()
        assert state_dict["redirect_url"] == redirect_url

    def test_properly_adds_user_to_groups_from_token_on_login(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_OPEN_ID_IS_AUTHORITY_FOR_USER_GROUPS", True):
            user = self.find_or_create_user("testing@e.com")
            user.email = "testing@e.com"
            user.service = app.config["SPIFFWORKFLOW_BACKEND_AUTH_CONFIGS"][0]["uri"]
            db.session.add(user)
            db.session.commit()

            access_token = user.encode_auth_token(
                {
                    "groups": ["group_one", "group_two"],
                    "iss": app.config["SPIFFWORKFLOW_BACKEND_AUTH_CONFIGS"][0]["uri"],
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

            access_token = user.encode_auth_token(
                {
                    "groups": ["group_one"],
                    "iss": app.config["SPIFFWORKFLOW_BACKEND_AUTH_CONFIGS"][0]["uri"],
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
        client: FlaskClient,
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
        client: FlaskClient,
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
        assert response.location.startswith(auth_uri)
        assert re.search(r"\bredirect_uri=" + re.escape(login_return_uri), response.location) is not None

    def test_raises_error_if_invalid_redirect_url(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        redirect_url = "http://www.bad_url.com/test-redirect-dne"
        response = client.get(
            f"/v1.0/login?redirect_url={redirect_url}&authentication_identifier=DOES_NOT_MATTER",
        )
        assert response.status_code == 500
        assert response.json is not None
        assert response.json["message"].startswith("InvalidRedirectUrlError:")
