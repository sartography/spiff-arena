import ast
import base64
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.user import UserModel
import time
from flask.testing import FlaskClient
from flask.app import Flask

from spiffworkflow_backend.services.authentication_service import AuthenticationService

from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestAuthentication(BaseTest):
    def test_get_login_state(self) -> None:
        redirect_url = "http://example.com/"
        state = AuthenticationService.generate_state(redirect_url)
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
        user = self.find_or_create_user()
        access_token = user.encode_auth_token({
            "groups": ["group_one", "group_two"],
            "iss": app.config['SPIFFWORKFLOW_BACKEND_OPEN_ID_SERVER_URL'],
            "aud": "spiffworkflow-backend",
            "iat": round(time.time()),
            "exp": round(time.time()) + 1000,
        })
        response = client.post(
            f"/v1.0/login_with_access_token?access_token={access_token}",
        )
        assert response.status_code == 200
        username = access_token["sub"]

        user = UserModel.query.filter_by(username=username).first()
        print(f"user.groups: {user.groups}")

