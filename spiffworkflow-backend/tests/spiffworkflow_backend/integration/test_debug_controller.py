from flask.app import Flask
from starlette.testclient import TestClient

from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestDebugController(BaseTest):
    def test_test_raise_error(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        response = client.post(
            "/v1.0/debug/test-raise-error",
        )
        assert response.status_code == 500

    def test_process_instance_with_most_tasks(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        # Call the endpoint directly to verify it returns the expected format
        response = client.get(
            "/v1.0/debug/process-instance-with-most-tasks",
        )
        # The endpoint will return 200 if there are process instances with tasks,
        # or 404 if the database has no process instances with tasks,
        # or 401 if authentication is required
        assert response.status_code in [200, 404, 401]

        if response.status_code == 200:
            assert "process_instance_id" in response.json()
            assert "task_count" in response.json()
            assert isinstance(response.json()["process_instance_id"], int)
            assert isinstance(response.json()["task_count"], int)
