from flask.app import Flask
from flask.testing import FlaskClient

from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestHealthController(BaseTest):
    def test_status(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        response = client.get(
            "/v1.0/status",
        )
        assert response.status_code == 200
