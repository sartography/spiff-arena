from flask.app import Flask
from flask.testing import FlaskClient

from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestDebugController(BaseTest):
    def test_test_raise_error(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        response = client.post(
            "/v1.0/debug/test-raise-error",
        )
        assert response.status_code == 500
