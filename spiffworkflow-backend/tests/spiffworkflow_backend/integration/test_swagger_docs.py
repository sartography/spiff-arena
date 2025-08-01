from flask.app import Flask
from starlette.testclient import TestClient

from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestSwaggerDocs(BaseTest):
    def test_can_retrieve_swagger_docs_without_auth(
        self,
        app: Flask,
        client: TestClient,
    ) -> None:
        response = client.get("/v1.0/ui/")
        assert response.status_code == 200
