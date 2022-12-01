"""Test_authentication."""
from flask import Flask
from flask.testing import FlaskClient
from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestFaskOpenId(BaseTest):
    """An integrated Open ID that responds to openID requests
    by referencing a build in YAML file.  Useful for
    local development, testing, demos etc..."""

    def test_discovery_of_endpoints(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        response = client.get("/openid/.well-known/openid-configuration")
        discovered_urls = response.json
        assert "http://localhost/openid" == discovered_urls["issuer"]
        assert (
            "http://localhost/openid/auth" == discovered_urls["authorization_endpoint"]
        )
        assert "http://localhost/openid/token" == discovered_urls["token_endpoint"]

    def test_get_login_page(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        # It should be possible to get to a login page
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

        code = (
            "c3BpZmZ3b3JrZmxvdy1iYWNrZW5kOkpYZVFFeG0wSmhRUEx1bWdIdElJcWY1MmJEYWxIejBx"
        )
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {code}",
        }
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_url": "http://localhost:7000/v1.0/login_return",
        }
        response = client.post("/openid/token", data=data, headers=headers)
        assert response
