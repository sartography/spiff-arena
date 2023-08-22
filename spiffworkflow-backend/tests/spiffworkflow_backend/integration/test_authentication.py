import ast
import base64
import time

from flask.app import Flask
from flask.testing import FlaskClient
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.user import UserModel
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
        user = self.find_or_create_user("testing@e.com")
        user.email = "testing@e.com"
        user.service = app.config["SPIFFWORKFLOW_BACKEND_OPEN_ID_SERVER_URL"]
        db.session.add(user)
        db.session.commit()

        access_token = user.encode_auth_token(
            {
                "groups": ["group_one", "group_two"],
                "iss": app.config["SPIFFWORKFLOW_BACKEND_OPEN_ID_SERVER_URL"],
                "aud": "spiffworkflow-backend",
                "iat": round(time.time()),
                "exp": round(time.time()) + 1000,
            }
        )
        response = client.post(
            f"/v1.0/login_with_access_token?access_token={access_token}",
        )
        assert response.status_code == 200
        assert len(user.groups) == 3
        group_identifiers = [g.identifier for g in user.groups]
        assert sorted(group_identifiers) == ["everybody", "group_one", "group_two"]

        access_token = user.encode_auth_token(
            {
                "groups": ["group_one"],
                "iss": app.config["SPIFFWORKFLOW_BACKEND_OPEN_ID_SERVER_URL"],
                "aud": "spiffworkflow-backend",
                "iat": round(time.time()),
                "exp": round(time.time()) + 1000,
            }
        )
        response = client.post(
            f"/v1.0/login_with_access_token?access_token={access_token}",
        )
        assert response.status_code == 200
        user = UserModel.query.filter_by(username=user.username).first()
        assert len(user.groups) == 2
        group_identifiers = [g.identifier for g in user.groups]
        assert sorted(group_identifiers) == ["everybody", "group_one"]
