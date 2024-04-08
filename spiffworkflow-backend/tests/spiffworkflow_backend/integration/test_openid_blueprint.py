import base64

import jwt
from flask import Flask
from flask.testing import FlaskClient

from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestOpenidBlueprint(BaseTest):
    """An integrated Open ID that responds to openID requests.

    By referencing a build in YAML file.  Useful for
    local development, testing, demos etc...
    """

    def test_discovery_of_endpoints(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        """Test discovery endpoints."""

        # SPIFFWORKFLOW_BACKEND_URL is set to http://localhost in unit_testing.py, but we ignore it anyway. See mock below.
        response = client.get("/openid/.well-known/openid-configuration")
        discovered_urls = response.json
        assert "http://localhost/openid" == discovered_urls["issuer"]
        assert "http://localhost/openid/auth" == discovered_urls["authorization_endpoint"]
        assert "http://localhost/openid/token" == discovered_urls["token_endpoint"]

        with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_URL", None):
            response = client.get("/openid/.well-known/openid-configuration")
            discovered_urls = response.json
            # in unit tests, request.host_url will not have the port but it will have it in actual localhost flask server
            assert "http://localhost/openid" == discovered_urls["issuer"]
            assert "http://localhost/openid/auth" == discovered_urls["authorization_endpoint"]
            assert "http://localhost/openid/token" == discovered_urls["token_endpoint"]

    def test_get_login_page(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        """It should be possible to get to a login page."""
        data = {"state": {"bubblegum": 1, "daydream": 2}}
        response = client.get("/openid/auth", query_string=data)
        assert b"<h2>Login</h2>" in response.data
        assert b"bubblegum" in response.data

    def test_get_token(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        code = "testadmin1:1234123412341234"

        """It should be possible to get a token."""
        backend_basic_auth_string = code
        backend_basic_auth_bytes = bytes(backend_basic_auth_string, encoding="ascii")
        backend_basic_auth = base64.b64encode(backend_basic_auth_bytes)
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {backend_basic_auth.decode('utf-8')}",
        }
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_url": "http://localhost:7000/v1.0/login_return",
        }
        response = client.post("/openid/token", data=data, headers=headers)
        assert response.status_code == 200
        assert response.is_json
        assert "access_token" in response.json
        assert "id_token" in response.json
        assert "refresh_token" in response.json

        decoded_token = jwt.decode(response.json["id_token"], options={"verify_signature": False})
        assert "iss" in decoded_token
        assert "email" in decoded_token
