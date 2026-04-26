from flask.app import Flask
from starlette.testclient import TestClient

from spiffworkflow_backend.models.task import TaskModel
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


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
        # Create a process model with fewer tasks
        process_model1 = load_test_spec(
            process_model_id="test_group/model_with_few_tasks",
            bpmn_file_name="data_stores.bpmn",
            process_model_source_directory="data_stores",
        )
        process_instance1 = self.create_process_instance_from_process_model(process_model1)
        processor1 = ProcessInstanceProcessor(process_instance1)
        processor1.do_engine_steps(save=True)

        # Create another process model with more tasks
        process_model2 = load_test_spec(
            process_model_id="test_group/model_with_more_tasks",
            bpmn_file_name="manual_task.bpmn",
            process_model_source_directory="manual_task",
        )
        process_instance2 = self.create_process_instance_from_process_model(process_model2)
        processor2 = ProcessInstanceProcessor(process_instance2)
        processor2.do_engine_steps(save=True)
        task_count = TaskModel.query.filter_by(process_instance_id=process_instance2.id).count()

        # Create a few more instances with fewer tasks to make sure our endpoint works correctly
        for _ in range(2):
            process_instance = self.create_process_instance_from_process_model(process_model1)
            processor = ProcessInstanceProcessor(process_instance)
            processor.do_engine_steps(save=True)

        # Call the endpoint and check the response
        response = client.get(
            "/v1.0/debug/process-instance-with-most-tasks",
        )

        assert response.status_code == 200

        assert "process_instance_id" in response.json()
        assert "task_count" in response.json()

        # Verify that the endpoint returns the process instance with the most tasks
        assert response.json()["process_instance_id"] == process_instance2.id
        assert response.json()["task_count"] == task_count
