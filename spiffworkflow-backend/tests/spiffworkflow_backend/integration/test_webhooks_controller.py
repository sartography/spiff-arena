import json
from hashlib import sha256
from hmac import HMAC

from connexion import FlaskApp  # type: ignore
from flask.app import Flask
from flask.testing import FlaskClient

from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestWebhooksController(BaseTest):
    def test_webhook_runs_configured_process_model(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        load_test_spec(
            "test_group/simple_script",
            process_model_source_directory="simple_script",
        )
        request_data = json.dumps({"body": "THIS IS OUR REQEST"})
        encoded_signature = self._create_encoded_signature(app, request_data)

        response = client.post(
            "/v1.0/webhook",
            headers={"X-Hub-Signature-256": f"sha256={encoded_signature}", "Content-type": "application/json"},
            data=request_data,
        )
        assert response.status_code == 200

    def _create_encoded_signature(self, app: FlaskApp, request_data: str) -> str:
        secret = app.config["SPIFFWORKFLOW_BACKEND_GITHUB_WEBHOOK_SECRET"].encode()
        return HMAC(key=secret, msg=request_data.encode(), digestmod=sha256).hexdigest()
