import json
import time
from unittest.mock import patch

import pytest
from flask.app import Flask
from SpiffWorkflow.util.task import TaskState  # type: ignore

from spiffworkflow_backend.models.future_task import FutureTaskModel
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.service_task_delegate import UncaughtServiceTaskError
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestServiceTaskRetries(BaseTest):
    def test_service_task_retries_on_failure(self, app: Flask, with_db_and_bpmn_file_cleanup: None) -> None:
        process_model = load_test_spec(
            process_model_id="test_group/retries",
            bpmn_file_name="retries.bpmn",
            process_model_source_directory="retries",
        )
        process_instance = self.create_process_instance_from_process_model(process_model=process_model)
        processor = ProcessInstanceProcessor(process_instance)
        processor.bpmn_process_instance.data["process_instance_id"] = process_instance.id

        # Mock connector proxy to return a 500 error
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 500
            mock_get.return_value.headers = {"Content-Type": "application/json"}
            mock_get.return_value.ok = False
            mock_get.return_value.text = json.dumps(
                {
                    "command_response": {"body": "{}", "http_status": 500},
                    "command_response_version": 2,
                    "error": {"error_code": "HttpError500", "message": "Server Error"},
                }
            )

            # Mock send_task to avoid RabbitMQ connection errors
            with patch("celery.current_app.send_task"):
                with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_CELERY_ENABLED", True):
                    processor.do_engine_steps(save=True)

        # Check task state.
        tasks = processor.bpmn_process_instance.get_tasks()
        service_task = [t for t in tasks if t.task_spec.bpmn_id == "ServiceTask_1"][0]
        assert service_task.state == TaskState.STARTED
        assert service_task.data.get("spiff__retry_count") == 2
        assert "spiff__retry_at" in service_task.data

        # Check if FutureTask was created
        future_task = FutureTaskModel.query.filter_by(guid=str(service_task.id)).first()
        assert future_task is not None
        assert future_task.completed is False

    def test_service_task_retries_when_retry_at_is_due(self, app: Flask, with_db_and_bpmn_file_cleanup: None) -> None:
        process_model = load_test_spec(
            process_model_id="test_group/retries",
            bpmn_file_name="retries.bpmn",
            process_model_source_directory="retries",
        )
        process_instance = self.create_process_instance_from_process_model(process_model=process_model)
        processor = ProcessInstanceProcessor(process_instance)
        processor.bpmn_process_instance.data["process_instance_id"] = process_instance.id

        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 500
            mock_get.return_value.headers = {"Content-Type": "application/json"}
            mock_get.return_value.ok = False
            mock_get.return_value.text = json.dumps(
                {
                    "command_response": {"body": "{}", "http_status": 500},
                    "command_response_version": 2,
                    "error": {"error_code": "HttpError500", "message": "Server Error"},
                }
            )

            with patch("celery.current_app.send_task"):
                with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_CELERY_ENABLED", True):
                    processor.do_engine_steps(save=True)

                tasks = processor.bpmn_process_instance.get_tasks()
                service_task = [t for t in tasks if t.task_spec.bpmn_id == "ServiceTask_1"][0]
                assert service_task.state == TaskState.STARTED
                assert service_task.data.get("spiff__retry_count") == 2

                service_task.data["spiff__retry_at"] = round(time.time()) - 1
                with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_CELERY_ENABLED", True):
                    processor.do_engine_steps(save=True)

        assert mock_get.call_count == 2
        assert service_task.state == TaskState.STARTED
        assert service_task.data.get("spiff__retry_count") == 1
        assert "spiff__retry_at" in service_task.data

    def test_service_task_fails_after_exhausting_retries(self, app: Flask, with_db_and_bpmn_file_cleanup: None) -> None:
        process_model = load_test_spec(
            process_model_id="test_group/retries",
            bpmn_file_name="retries.bpmn",
            process_model_source_directory="retries",
        )
        process_instance = self.create_process_instance_from_process_model(process_model=process_model)
        processor = ProcessInstanceProcessor(process_instance)
        processor.bpmn_process_instance.data["process_instance_id"] = process_instance.id

        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 500
            mock_get.return_value.headers = {"Content-Type": "application/json"}
            mock_get.return_value.ok = False
            mock_get.return_value.text = json.dumps(
                {
                    "command_response": {"body": "{}", "http_status": 500},
                    "command_response_version": 2,
                    "error": {"error_code": "HttpError500", "message": "Server Error"},
                }
            )

            with patch("celery.current_app.send_task"):
                # First attempt
                with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_CELERY_ENABLED", True):
                    processor.do_engine_steps(save=True)
                tasks = processor.bpmn_process_instance.get_tasks()
                service_task = [t for t in tasks if t.task_spec.bpmn_id == "ServiceTask_1"][0]
                assert service_task.data.get("spiff__retry_count") == 2

                # Second attempt
                service_task._set_state(TaskState.READY)
                with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_CELERY_ENABLED", True):
                    processor.do_engine_steps(save=True)
                assert service_task.data.get("spiff__retry_count") == 1

                # Third attempt
                service_task._set_state(TaskState.READY)
                with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_CELERY_ENABLED", True):
                    processor.do_engine_steps(save=True)
                assert service_task.data.get("spiff__retry_count") == 0

                # Final attempt - should exhaust retries and raise UncaughtServiceTaskError
                service_task._set_state(TaskState.READY)
                from spiffworkflow_backend.services.workflow_execution_service import WorkflowExecutionServiceError

                with pytest.raises((UncaughtServiceTaskError, WorkflowExecutionServiceError)):
                    processor.do_engine_steps(save=True)

        assert service_task.state == TaskState.ERROR

    def test_service_task_does_not_retry_on_permanent_failure(self, app: Flask, with_db_and_bpmn_file_cleanup: None) -> None:
        process_model = load_test_spec(
            process_model_id="test_group/retries",
            bpmn_file_name="retries.bpmn",
            process_model_source_directory="retries",
        )
        process_instance = self.create_process_instance_from_process_model(process_model=process_model)
        processor = ProcessInstanceProcessor(process_instance)
        processor.bpmn_process_instance.data["process_instance_id"] = process_instance.id

        # Mock connector proxy to return a 400 error (permanent)
        # ServiceTaskDelegate.check_for_errors will raise UncaughtServiceTaskError for status >= 300
        # unless it is caught by an error event.
        # In our case, 400 is NOT transient according to ServiceTaskDelegate.is_transient_error.
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 400
            mock_get.return_value.headers = {"Content-Type": "application/json"}
            mock_get.return_value.ok = False
            mock_get.return_value.text = json.dumps(
                {
                    "command_response": {"body": "{}", "http_status": 400},
                    "command_response_version": 2,
                    "error": {"error_code": "HttpError400", "message": "Bad Request"},
                }
            )

            from spiffworkflow_backend.services.workflow_execution_service import WorkflowExecutionServiceError

            with pytest.raises((UncaughtServiceTaskError, WorkflowExecutionServiceError)):
                processor.do_engine_steps(save=True)

        tasks = processor.bpmn_process_instance.get_tasks()
        service_task = [t for t in tasks if t.task_spec.bpmn_id == "ServiceTask_1"][0]
        assert service_task.state == TaskState.ERROR
        assert "spiff__retry_count" not in service_task.data
