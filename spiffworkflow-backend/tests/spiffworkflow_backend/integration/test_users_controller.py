"""test_users_controller."""

from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from spiffworkflow_backend.models.user import UserModel
from flask.testing import FlaskClient
from flask.app import Flask


class TestUsersController(BaseTest):
    """TestUsersController."""

    def test_user_search_returns_a_user(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_user_search_returns_a_user."""
        self.find_or_create_user(username="aa")
        self.find_or_create_user(username="ab")
        self.find_or_create_user(username="abc")
        self.find_or_create_user(username="ac")

        self._assert_search_has_count(client, with_super_admin_user, 'aa', 1)
        self._assert_search_has_count(client, with_super_admin_user, 'ab', 2)
        self._assert_search_has_count(client, with_super_admin_user, 'ac', 1)
        self._assert_search_has_count(client, with_super_admin_user, 'ad', 0)
        self._assert_search_has_count(client, with_super_admin_user, 'a', 4)

    def _assert_search_has_count(self, client: FlaskClient, with_super_admin_user: UserModel, username_prefix: str, expected_count: int) -> None:
        """_assert_search_has_count."""
        response = client.get(
            f"/v1.0/users/search?username_prefix={username_prefix}",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200
        assert response.json
        assert response.json['users'] is not None
        assert response.json['username_prefix'] == username_prefix
        assert len(response.json['users']) == expected_count
