from flask.app import Flask
from flask.testing import FlaskClient
from spiffworkflow_backend.models.user import UserModel

from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestUsersController(BaseTest):
    def test_user_search_returns_a_user(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        self.find_or_create_user(username="aa")
        self.find_or_create_user(username="ab")
        self.find_or_create_user(username="abc")
        self.find_or_create_user(username="ac")

        self._assert_search_has_count(client, with_super_admin_user, "aa", 1)
        self._assert_search_has_count(client, with_super_admin_user, "ab", 2)
        self._assert_search_has_count(client, with_super_admin_user, "ac", 1)
        self._assert_search_has_count(client, with_super_admin_user, "ad", 0)
        self._assert_search_has_count(client, with_super_admin_user, "a", 4)

    def _assert_search_has_count(
        self,
        client: FlaskClient,
        with_super_admin_user: UserModel,
        username_prefix: str,
        expected_count: int,
    ) -> None:
        response = client.get(
            f"/v1.0/users/search?username_prefix={username_prefix}",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200
        assert response.json
        assert response.json["users"] is not None
        assert response.json["username_prefix"] == username_prefix
        assert len(response.json["users"]) == expected_count
