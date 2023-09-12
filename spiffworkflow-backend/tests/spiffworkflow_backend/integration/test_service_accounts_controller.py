import json

from flask.app import Flask
from flask.testing import FlaskClient
from spiffworkflow_backend.models.service_account import ServiceAccountModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.user_service import UserService

from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestServiceAccountsController(BaseTest):
    def test_can_create_a_service_account(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        api_key_name = "heyhey"
        response = client.post(
            "/v1.0/service-accounts",
            content_type="application/json",
            data=json.dumps({"name": api_key_name}),
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 201
        assert response.json is not None
        assert response.json["api_key"] is not None

        api_key = response.json["api_key"]
        service_account = ServiceAccountModel.query.filter_by(api_key=api_key).first()
        assert service_account is not None
        assert service_account.created_by_user_id == with_super_admin_user.id
        assert service_account.name == api_key_name

        # ci and local set different permissions for the admin user so figure out dynamically
        admin_permissions = sorted(UserService.get_permission_targets_for_user(with_super_admin_user))
        service_account_permissions = sorted(
            UserService.get_permission_targets_for_user(service_account.user, check_groups=False)
        )
        assert admin_permissions == service_account_permissions

        # ensure service account can actually access the api
        response = client.post(
            "/v1.0/service-accounts",
            content_type="application/json",
            data=json.dumps({"name": "heyhey1"}),
            headers={"X-API-KEY": service_account.api_key},
        )
        assert response.status_code == 201
        assert response.json is not None
        assert response.json["api_key"] is not None
