"""Tests for the process model import functionality.

Note: These tests expect the backend service to be restarted after making changes
to the API definitions. The tests will fail with 500 errors until the backend is
restarted with the new API definitions.
"""

from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from flask.app import Flask
from starlette.testclient import TestClient

from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.file_system_service import FileSystemService
from spiffworkflow_backend.services.process_model_import_service import ProcessModelImportService
from spiffworkflow_backend.services.spec_file_service import SpecFileService
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestProcessModelImportController(BaseTest):
    def test_process_model_import_from_filestore_package_preserves_process_model_directories(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        bpmn = Path("tests/data/simple_script/simple_script.bpmn").read_text()
        package = {
            "project_id": "files-project",
            "snapshot_id": "snapshot-1",
            "files": [
                {"path": "main/main.bpmn", "content": bpmn.replace("Process_SimpleScript", "main_process")},
                {"path": "called/activity.bpmn", "content": bpmn.replace("Process_SimpleScript", "called_activity")},
            ],
        }

        process_models = ProcessModelImportService.import_from_filestore_package(package, "filestore")

        assert [process_model.id for process_model in process_models] == ["filestore/called", "filestore/main"]
        assert FileSystemService.get_data(process_models[0], "activity.bpmn").decode().find("called_activity") > -1
        assert FileSystemService.get_data(process_models[1], "main.bpmn").decode().find("main_process") > -1

    def test_process_model_import_from_filestore_package_names_root_model_without_moving_files(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        bpmn = Path("tests/data/simple_script/simple_script.bpmn").read_text()
        project_id = "7638D555-2E7F-48F0-8036-0C7Cb58B9C5A"
        package = {
            "project_id": project_id,
            "project_name": "Test4",
            "snapshot_id": "snapshot-1",
            "files": [
                {"path": "test4.bpmn", "content": bpmn},
            ],
        }

        process_models = ProcessModelImportService.import_from_filestore_package(package, "filestore")

        assert len(process_models) == 1
        assert process_models[0].id == f"filestore/test4-{project_id.lower()}"
        assert process_models[0].display_name == f"Test4 {project_id}"
        assert FileSystemService.get_data(process_models[0], "test4.bpmn").decode().find("Process_SimpleScript") > -1

    def test_process_model_import_from_filestore_file_update_names_root_model(
        self,
        app: Flask,
        monkeypatch: pytest.MonkeyPatch,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        bpmn = Path("tests/data/simple_script/simple_script.bpmn").read_text()
        response = MagicMock(status_code=200)
        response.json.return_value = {"content": bpmn}

        monkeypatch.setattr(
            "spiffworkflow_backend.services.process_model_import_service.FilestoreClientService.headers_for_request",
            MagicMock(return_value={"SpiffWorkflow-Tenant": "default"}),
        )
        monkeypatch.setattr(
            "spiffworkflow_backend.services.process_model_import_service.requests.get",
            MagicMock(return_value=response),
        )

        process_models = ProcessModelImportService.import_filestore_file_update(
            {
                "project_id": "7638D555-2E7F-48F0-8036-0C7Cb58B9C5A",
                "project_name": "Test4",
                "path": "test4.bpmn",
                "file_url": "http://files.test/v1/projects/7638D555/files/test4.bpmn",
            },
            "filestore",
        )

        assert [process_model.id for process_model in process_models] == ["filestore/test4-7638d555-2e7f-48f0-8036-0c7cb58b9c5a"]
        assert FileSystemService.get_data(process_models[0], "test4.bpmn").decode().find("Process_SimpleScript") > -1

    def test_process_model_import_from_filestore_file_update_only_updates_that_file(
        self,
        app: Flask,
        monkeypatch: pytest.MonkeyPatch,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        bpmn = Path("tests/data/simple_script/simple_script.bpmn").read_text()
        load_test_spec(
            "playground/samwise/hello",
            bpmn_file_name="simple_script.bpmn",
            process_model_source_directory="simple_script",
        )
        load_test_spec(
            "playground/gandalf/secret",
            bpmn_file_name="hello_world.bpmn",
            process_model_source_directory="hello_world",
        )
        response = MagicMock(status_code=200)
        response.json.return_value = {"content": bpmn.replace("Process_SimpleScript", "Process_Hello_Samwise")}
        update_file = MagicMock(wraps=SpecFileService.update_file)

        monkeypatch.setattr(
            "spiffworkflow_backend.services.process_model_import_service.FilestoreClientService.headers_for_request",
            MagicMock(return_value={"SpiffWorkflow-Tenant": "default"}),
        )
        monkeypatch.setattr(
            "spiffworkflow_backend.services.process_model_import_service.requests.get",
            MagicMock(return_value=response),
        )
        monkeypatch.setattr(SpecFileService, "update_file", update_file)

        process_models = ProcessModelImportService.import_filestore_file_update(
            {
                "project_id": "playground",
                "path": "samwise/hello/simple_script.bpmn",
                "file_url": "http://files.test/v1/projects/playground/files/samwise/hello/simple_script.bpmn",
            },
            "playground",
        )

        assert [process_model.id for process_model in process_models] == ["playground/samwise/hello"]
        assert update_file.call_count == 1
        assert update_file.call_args.args[0].id == "playground/samwise/hello"
        assert update_file.call_args.args[1] == "simple_script.bpmn"

    def test_process_model_import_from_github(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test importing a process model from a GitHub URL."""
        process_group_id = "test_group"

        # Create a process group first
        self.create_process_group_with_api(
            client=client, user=with_super_admin_user, process_group_id=process_group_id, display_name="Test Group"
        )

        # Mock the ProcessModelImportService.import_from_github_url method
        mock_process_model = ProcessModelInfo(
            id=f"{process_group_id}/imported_model",
            display_name="Imported Model",
            description="Imported from GitHub",
            primary_process_id="imported_process",
            primary_file_name="imported_model.bpmn",
        )

        with patch.object(ProcessModelImportService, "import_from_github_url", return_value=mock_process_model) as mock_import:
            # Make a request to the import endpoint
            repository_url = "https://github.com/sartography/example-process-models/tree/main/examples/0-1-minimal-example"
            response = client.post(
                f"/v1.0/process-model-import/{process_group_id}",
                json={"repository_url": repository_url},
                headers=self.logged_in_headers(with_super_admin_user),
            )

            # Check the response status code
            assert response.status_code == 201

            # Verify the response data
            response_data = response.json()
            assert "process_model" in response_data
            assert response_data["process_model"]["id"] == f"{process_group_id}/imported_model"
            assert response_data["process_model"]["display_name"] == "Imported Model"
            assert response_data["process_model"]["description"] == "Imported from GitHub"
            assert response_data["import_source"] == repository_url

            # Verify the service method was called correctly
            mock_import.assert_called_once_with(url=repository_url, process_group_id=process_group_id)

    def test_process_model_import_missing_url(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test importing a process model with a missing URL."""
        process_group_id = "test_group"

        # Create a process group first
        self.create_process_group_with_api(
            client=client, user=with_super_admin_user, process_group_id=process_group_id, display_name="Test Group"
        )

        # Make a request to the import endpoint without a repository_url
        response = client.post(
            f"/v1.0/process-model-import/{process_group_id}",
            json={},
            headers=self.logged_in_headers(with_super_admin_user),
        )

        # Fix the URL to use the correct API endpoint
        # Check the response status code
        assert response.status_code == 400

        # Verify the error message
        response_data = response.json()
        assert response_data["title"] == "Bad Request"
        assert "'repository_url' is a required property" in response_data["detail"]

    def test_process_model_import_invalid_group(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test importing a process model to a non-existent group."""
        process_group_id = "nonexistent_group"

        repository_url = "https://github.com/sartography/example-process-models/tree/main/examples/0-1-minimal-example"
        response = client.post(
            f"/v1.0/process-model-import/{process_group_id}",
            json={"repository_url": repository_url},
            headers=self.logged_in_headers(with_super_admin_user),
        )

        # Check the response status code
        assert response.status_code == 500

        # Verify the error message
        response_data = response.json()
        assert "error_code" in response_data
        assert response_data["error_code"] == "internal_server_error"
        assert "process_group_not_found" in response_data["message"]

    def test_process_model_import_from_model_alias(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test importing a process model from a marketplace model alias."""
        process_group_id = "test_group"

        # Create a process group first
        self.create_process_group_with_api(
            client=client, user=with_super_admin_user, process_group_id=process_group_id, display_name="Test Group"
        )

        # Mock the ProcessModelImportService.import_from_model_alias method
        mock_process_model = ProcessModelInfo(
            id=f"{process_group_id}/timer_events",
            display_name="Timer Events",
            description="Imported from marketplace: timer-events",
            primary_process_id="timer_events_process",
            primary_file_name="timer-events.bpmn",
        )

        with (
            patch.object(ProcessModelImportService, "is_model_alias", return_value=True),
            patch.object(ProcessModelImportService, "import_from_model_alias", return_value=mock_process_model) as mock_import,
        ):
            # Make a request to the import endpoint with a model alias
            model_alias = "timer-events"
            response = client.post(
                f"/v1.0/process-model-import/{process_group_id}",
                json={"repository_url": model_alias},
                headers=self.logged_in_headers(with_super_admin_user),
            )

            # Check the response status code
            assert response.status_code == 201

            # Verify the response data
            response_data = response.json()
            assert "process_model" in response_data
            assert response_data["process_model"]["id"] == f"{process_group_id}/timer_events"
            assert response_data["process_model"]["display_name"] == "Timer Events"
            assert response_data["process_model"]["description"] == "Imported from marketplace: timer-events"
            assert response_data["import_source"] == model_alias

            # Verify the service method was called correctly
            mock_import.assert_called_once_with(alias=model_alias, process_group_id=process_group_id)

    def test_is_model_alias(self) -> None:
        """Test the is_model_alias method."""
        # Valid model aliases
        assert ProcessModelImportService.is_model_alias("timer-events") is True
        assert ProcessModelImportService.is_model_alias("simple_example") is True
        assert ProcessModelImportService.is_model_alias("example123") is True

        # Invalid model aliases
        assert ProcessModelImportService.is_model_alias("https://github.com/example") is False
        assert ProcessModelImportService.is_model_alias("example with spaces") is False
        assert ProcessModelImportService.is_model_alias("example/with/slashes") is False

    def test_get_marketplace_url(self, app: Flask) -> None:
        with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_MODEL_MARKETPLACE_URL", "https://custom-marketplace.example.com"):
            assert ProcessModelImportService.get_marketplace_url() == "https://custom-marketplace.example.com"

        # default
        assert ProcessModelImportService.get_marketplace_url() == "https://model-marketplace.spiff.works"
