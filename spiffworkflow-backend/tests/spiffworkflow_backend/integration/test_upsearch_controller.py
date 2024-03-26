import pytest
from flask.app import Flask
from flask.testing import FlaskClient
from spiffworkflow_backend.models.user import UserModel

from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestUpsearchControllerController(BaseTest):
    @pytest.mark.parametrize(
        "location,expected",
        [
            ("a/b/c/d", ["a/b/c/d", "a/b/c", "a/b", "a", ""]),
            ("a", ["a", ""]),
            ("", [""]),
        ],
    )
    def test_return_upsearch_locations_for_path(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
        location: str,
        expected: list[str],
    ) -> None:
        response = client.get(
            f"/v1.0/upsearch-locations?location={location}", headers=self.logged_in_headers(with_super_admin_user)
        )

        assert response.status_code == 200
        assert "locations" in response.json
        assert response.json["locations"] == expected
