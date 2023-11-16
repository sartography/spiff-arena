import json

from flask.app import Flask
from flask.testing import FlaskClient
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.service_account_service import ServiceAccountService
from spiffworkflow_backend.services.user_service import UserService

from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestServiceAccounts(BaseTest):
    def test_can_create_a_service_account(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        api_key_name = "heyhey"
        service_account = ServiceAccountService.create_service_account(api_key_name, with_super_admin_user)

        assert service_account is not None
        assert service_account.created_by_user_id == with_super_admin_user.id
        assert service_account.name == api_key_name
        assert service_account.api_key is not None

        # ci and local set different permissions for the admin user so figure out dynamically
        admin_permissions = sorted(UserService.get_permission_targets_for_user(with_super_admin_user))
        service_account_permissions = sorted(
            UserService.get_permission_targets_for_user(service_account.user, check_groups=False)
        )
        assert admin_permissions == service_account_permissions

        # ensure service account can actually access the api
        post_body = {
            "key": "secret_key",
            "value": "hey_value",
        }
        response = client.post(
            "/v1.0/secrets",
            content_type="application/json",
            headers={"SpiffWorkflow-Api-Key": service_account.api_key},
            data=json.dumps(post_body),
        )
        assert response.status_code == 201
        assert response.json is not None
        assert response.json["key"] == post_body["key"]
