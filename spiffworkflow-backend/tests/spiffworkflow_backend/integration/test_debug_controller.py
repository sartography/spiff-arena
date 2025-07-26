from flask.app import Flask
from starlette.testclient import TestClient

from spiffworkflow_backend.models.task import TaskModel
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

    def test_system_info(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        response = client.get(
            "/v1.0/debug/system-info",
        )
        assert response.status_code == 200
        assert response.json()
        assert "platform" in response.json()
        assert "python_version" in response.json()

    def test_process_instance_with_most_tasks(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        # Create process models and instances with different numbers of tasks
        process_model1 = load_test_spec(
            process_model_id="test_group/model_with_few_tasks",
            bpmn_file_name="two_user_tasks.bpmn",
        )
        process_instance1 = self.create_process_instance_from_process_model(process_model1)
        processor1 = self.get_processor(process_instance1)
        processor1.do_engine_steps(save=True)

        # Create a second process instance with more tasks
        process_model2 = load_test_spec(
            process_model_id="test_group/model_with_many_tasks",
            bpmn_file_name="parallel_tasks.bpmn",
        )
        process_instance2 = self.create_process_instance_from_process_model(process_model2)
        processor2 = self.get_processor(process_instance2)
        processor2.do_engine_steps(save=True)

        # Add some additional tasks to process_instance2 to ensure it has more tasks
        # This is a simple way to ensure a specific instance has the most tasks
        task_count1 = TaskModel.query.filter_by(process_instance_id=process_instance1.id).count()
        task_count2 = TaskModel.query.filter_by(process_instance_id=process_instance2.id).count()

        # Call the endpoint and check the response
        response = client.get(
            "/v1.0/debug/process-instance-with-most-tasks",
        )
        assert response.status_code == 200
        assert response.json()
        assert "process_instance_id" in response.json()
        assert "task_count" in response.json()

        # The process instance with more tasks should be returned
        expected_instance_id = process_instance2.id if task_count2 > task_count1 else process_instance1.id
        expected_task_count = max(task_count1, task_count2)

        assert response.json()["process_instance_id"] == expected_instance_id
        assert response.json()["task_count"] == expected_task_count
