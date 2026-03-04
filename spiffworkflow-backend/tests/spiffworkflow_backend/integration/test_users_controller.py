from flask.app import Flask
from starlette.testclient import TestClient

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.models.user_group_assignment import UserGroupAssignmentModel
from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestUsersController(BaseTest):
    def test_user_search_returns_a_user(
        self,
        app: Flask,
        client: TestClient,
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
        client: TestClient,
        with_super_admin_user: UserModel,
        username_prefix: str,
        expected_count: int,
    ) -> None:
        response = client.get(
            f"/v1.0/users/search?username_prefix={username_prefix}",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200
        assert response.json()
        assert response.json()["users"] is not None
        assert response.json()["username_prefix"] == username_prefix
        assert len(response.json()["users"]) == expected_count

    def test_users_in_group_returns_users(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        group_name = "coolest_group"

        # Create a group and add users to it
        group = GroupModel(identifier=group_name)
        user_a = self.find_or_create_user(username="user_a")
        user_b = self.find_or_create_user(username="user_b")

        db.session.add(group)
        db.session.flush()  # ensures group.id is populated

        db.session.add_all(
            [
                UserGroupAssignmentModel(user_id=user_a.id, group_id=group.id),
                UserGroupAssignmentModel(user_id=user_b.id, group_id=group.id),
            ]
        )
        db.session.commit()

        response = client.get(
            f"/v1.0/users/in-group?group_name={group_name}",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200

        body = response.json()
        assert isinstance(body, list)
        assert len(body) == 2

        emails = sorted([str(u["email"]) for u in body])
        assert emails == sorted([str(user_a.email), str(user_b.email)])

        # spot-check shape
        for u in body:
            assert "email" in u
            assert "display_name" in u
            assert "username" in u
