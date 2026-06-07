import json
from hashlib import sha256
from hmac import HMAC
from unittest.mock import Mock

from connexion import FlaskApp
from flask.app import Flask
from starlette.testclient import TestClient

from spiffworkflow_backend.routes import webhooks_controller
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestWebhooksController(BaseTest):
    def test_webhook_runs_configured_process_model(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        load_test_spec(
            "test_group/simple_script",
            process_model_source_directory="simple_script",
        )
        request_data = {"body": "THIS IS OUR REQEST"}
        encoded_signature = self._create_encoded_signature(app, json.dumps(request_data))

        response = client.post(
            "/v1.0/webhook",
            headers={"X-Hub-Signature-256": f"sha256={encoded_signature}", "Content-Type": "application/json"},
            content=json.dumps(request_data).encode(),
        )
        assert response.status_code == 200

    def test_filestore_webhook_fetches_package_with_tenant_header(
        self,
        client: TestClient,
        monkeypatch,
    ) -> None:
        package = {"project_id": "project-1", "snapshot_id": "snapshot-1", "files": []}
        package_response = Mock(status_code=200)
        package_response.json.return_value = package
        get = Mock(return_value=package_response)
        import_package = Mock(return_value=[])
        commit = Mock()
        monkeypatch.setattr(webhooks_controller.requests, "get", get)
        monkeypatch.setattr(webhooks_controller.ProcessModelImportService, "import_from_filestore_package", import_package)
        monkeypatch.setattr(webhooks_controller.GitService, "commit_on_save", commit)

        response = client.post(
            "/v1.0/filestore-webhook",
            headers={"Content-Type": "application/json"},
            content=json.dumps({
                "event": "snapshot.created",
                "tenant_id": "gsa",
                "arena_package_url": "https://files.example/package",
            }).encode(),
        )

        assert response.status_code == 200
        get.assert_called_once_with(
            "https://files.example/package",
            headers={"SpiffWorkflow-Tenant": "gsa"},
            timeout=30,
        )
        import_package.assert_called_once()

    def _create_encoded_signature(self, app: FlaskApp, request_data: str) -> str:
        secret = app.config["SPIFFWORKFLOW_BACKEND_GITHUB_WEBHOOK_SECRET"].encode()
        return HMAC(key=secret, msg=request_data.encode(), digestmod=sha256).hexdigest()
