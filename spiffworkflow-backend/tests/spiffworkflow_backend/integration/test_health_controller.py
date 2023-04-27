from flask.app import Flask
from flask.testing import FlaskClient
from tests.spiffworkflow_backend.helpers.base_test import BaseTest

from spiffworkflow_backend.models.user import UserModel


class TestHealthController(BaseTest):
    """TestUsersController."""

    def test_status(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_user_search_returns_a_user."""
        response = client.get(
            f"/v1.0/status",
        )
        assert response.status_code == 200

    def test_test_raise_error(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_user_search_returns_a_user."""
        response = client.get(
            f"/v1.0/status/test-raise-error",
        )
        assert response.status_code == 500
