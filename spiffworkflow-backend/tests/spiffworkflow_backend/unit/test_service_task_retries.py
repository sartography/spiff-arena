import json
from typing import Any
from unittest.mock import patch

import pytest
from flask.app import Flask
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore
from SpiffWorkflow.util.task import TaskState  # type: ignore

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.future_task import FutureTaskModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance_event import ProcessInstanceEventModel
from spiffworkflow_backend.models.process_instance_event import ProcessInstanceEventType
from spiffworkflow_backend.models.task import TaskModel
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.service_task_delegate import UncaughtServiceTaskError
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestServiceTaskRetries(BaseTest):
    fake_now = 2_000_000_000

    def service_task_specs_in(self, value: object) -> list[dict]:
        if isinstance(value, dict):
            matches = []
            if value.get("bpmn_id") == "ServiceTask_1" and value.get("operation_name") == "http/GetRequest":
                matches.append(value)
            for child_value in value.values():
                matches.extend(self.service_task_specs_in(child_value))
            return matches
        if isinstance(value, list):
            matches = []
            for child_value in value:
                matches.extend(self.service_task_specs_in(child_value))
            return matches
        return []

    def load_retry_processor(self, bpmn_file_name: str = "retries.bpmn") -> tuple[ProcessInstanceProcessor, ProcessInstanceModel]:
        process_model = load_test_spec(
            process_model_id="test_group/retries",
            bpmn_file_name=bpmn_file_name,
            process_model_source_directory="retries",
        )
        process_instance = self.create_process_instance_from_process_model(process_model=process_model)
        processor = ProcessInstanceProcessor(process_instance)
        processor.bpmn_process_instance.data["process_instance_id"] = process_instance.id
        return processor, process_instance

    def get_service_task(self, processor: ProcessInstanceProcessor) -> SpiffTask:
        tasks = processor.bpmn_process_instance.get_tasks()
        return [t for t in tasks if t.task_spec.bpmn_id == "ServiceTask_1"][0]

    def patch_retry_time(self) -> tuple[Any, Any]:
        return (
            patch("spiffworkflow_backend.services.custom_service_task.time.time", return_value=self.fake_now),
            patch("spiffworkflow_backend.services.workflow_execution_service.time.time", return_value=self.fake_now),
        )

    def transient_failure_response(self, mock_get: Any) -> None:
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

    def proxy_success_with_upstream_failure_response(self, mock_response: Any, upstream_status: int = 500) -> None:
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.ok = True
        mock_response.text = json.dumps(
            {
                "command_response": {"body": "{}", "http_status": upstream_status},
                "command_response_version": 2,
            }
        )

    def test_service_task_retry_settings_are_serialized(self, app: Flask, with_db_and_bpmn_file_cleanup: None) -> None:
        processor, _process_instance = self.load_retry_processor()
        service_task_specs = self.service_task_specs_in(processor.serialize())

        assert len(service_task_specs) == 1
        assert service_task_specs[0]["retries"] == 3
        assert service_task_specs[0]["retry_backoff_base"] == 3

    def test_service_task_retry_backoff_base_can_be_overridden_in_bpmn(
        self, app: Flask, with_db_and_bpmn_file_cleanup: None
    ) -> None:
        processor, process_instance = self.load_retry_processor("retries_backoff_override.bpmn")

        service_task_specs = self.service_task_specs_in(processor.serialize())
        assert len(service_task_specs) == 1
        assert service_task_specs[0]["retry_backoff_base"] == 2

        with patch("requests.get") as mock_get:
            self.transient_failure_response(mock_get)
            custom_service_task_time, workflow_execution_service_time = self.patch_retry_time()
            with custom_service_task_time, workflow_execution_service_time:
                with patch("celery.current_app.send_task"):
                    with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_CELERY_ENABLED", True):
                        processor.do_engine_steps(save=True)

        service_task = self.get_service_task(processor)
        assert service_task.internal_data.get("spiff__retries_attempted") == 0
        assert service_task.internal_data.get("spiff__retry_at") == self.fake_now + 2
        assert process_instance.spiffworkflow_fully_initialized()

    def test_service_task_retries_on_failure(self, app: Flask, with_db_and_bpmn_file_cleanup: None) -> None:
        processor, _process_instance = self.load_retry_processor()

        with patch("requests.get") as mock_get:
            self.transient_failure_response(mock_get)
            custom_service_task_time, workflow_execution_service_time = self.patch_retry_time()
            with custom_service_task_time, workflow_execution_service_time:
                with patch("celery.current_app.send_task"):
                    with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_CELERY_ENABLED", True):
                        processor.do_engine_steps(save=True)

        service_task = self.get_service_task(processor)
        assert service_task.state == TaskState.STARTED
        assert service_task.internal_data.get("spiff__retries_attempted") == 0
        assert service_task.internal_data.get("spiff__retry_at") == self.fake_now + 3

        task_model = TaskModel.query.filter_by(guid=str(service_task.id)).one()
        assert task_model.end_in_seconds is None

        completion_event = ProcessInstanceEventModel.query.filter_by(
            task_guid=str(service_task.id),
            event_type=ProcessInstanceEventType.task_completed.value,
        ).first()
        assert completion_event is None

        future_task = FutureTaskModel.query.filter_by(guid=str(service_task.id)).first()
        assert future_task is not None
        assert future_task.completed is False

    def test_service_task_retries_on_upstream_failure_in_successful_proxy_response(
        self, app: Flask, with_db_and_bpmn_file_cleanup: None
    ) -> None:
        processor, _process_instance = self.load_retry_processor()

        with patch("requests.post") as mock_post:
            self.proxy_success_with_upstream_failure_response(mock_post.return_value)
            custom_service_task_time, workflow_execution_service_time = self.patch_retry_time()
            with custom_service_task_time, workflow_execution_service_time:
                with (
                    patch("celery.current_app.send_task"),
                    patch("spiffworkflow_backend.services.service_task_delegate.http_connector.does", return_value=False),
                ):
                    with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_CELERY_ENABLED", True):
                        processor.do_engine_steps(save=True)

        service_task = self.get_service_task(processor)
        assert service_task.state == TaskState.STARTED
        assert service_task.internal_data.get("spiff__retries_attempted") == 0
        assert service_task.internal_data.get("spiff__retry_at") == self.fake_now + 3

        future_task = FutureTaskModel.query.filter_by(guid=str(service_task.id)).first()
        assert future_task is not None
        assert future_task.completed is False

    def test_service_task_retries_when_retry_at_is_due(self, app: Flask, with_db_and_bpmn_file_cleanup: None) -> None:
        processor, process_instance = self.load_retry_processor()

        with patch("requests.get") as mock_get:
            self.transient_failure_response(mock_get)
            custom_service_task_time, workflow_execution_service_time = self.patch_retry_time()
            with custom_service_task_time, workflow_execution_service_time:
                with patch("celery.current_app.send_task"):
                    with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_CELERY_ENABLED", True):
                        processor.do_engine_steps(save=True)

                    assert process_instance.spiffworkflow_fully_initialized()

                    db.session.expire_all()
                    reloaded_process_instance = ProcessInstanceModel.query.filter_by(id=process_instance.id).one()
                    processor = ProcessInstanceProcessor(reloaded_process_instance)
                    service_task = self.get_service_task(processor)
                    assert service_task.state == TaskState.STARTED
                    assert service_task.task_spec.retries == 3
                    assert service_task.task_spec.retry_backoff_base == 3
                    assert service_task.internal_data.get("spiff__retries_attempted") == 0

                    service_task.internal_data["spiff__retry_at"] = self.fake_now - 1

                    with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_CELERY_ENABLED", True):
                        processor.do_engine_steps(save=True)

        assert mock_get.call_count == 2
        assert service_task.state == TaskState.STARTED
        assert service_task.internal_data.get("spiff__retries_attempted") == 1
        assert service_task.internal_data.get("spiff__retry_at") == self.fake_now + 9

    def test_service_task_fails_after_exhausting_retries(self, app: Flask, with_db_and_bpmn_file_cleanup: None) -> None:
        processor, _process_instance = self.load_retry_processor()

        with patch("requests.get") as mock_get:
            self.transient_failure_response(mock_get)
            custom_service_task_time, workflow_execution_service_time = self.patch_retry_time()
            with custom_service_task_time, workflow_execution_service_time:
                with patch("celery.current_app.send_task"):
                    with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_CELERY_ENABLED", True):
                        processor.do_engine_steps(save=True)

                    service_task = self.get_service_task(processor)
                    assert service_task.internal_data.get("spiff__retries_attempted") == 0
                    assert service_task.internal_data.get("spiff__retry_at") == self.fake_now + 3

                    service_task.internal_data["spiff__retry_at"] = self.fake_now - 1
                    with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_CELERY_ENABLED", True):
                        processor.do_engine_steps(save=True)
                    assert service_task.internal_data.get("spiff__retries_attempted") == 1
                    assert service_task.internal_data.get("spiff__retry_at") == self.fake_now + 9

                    service_task.internal_data["spiff__retry_at"] = self.fake_now - 1
                    with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_CELERY_ENABLED", True):
                        processor.do_engine_steps(save=True)
                    assert service_task.internal_data.get("spiff__retries_attempted") == 2
                    assert service_task.internal_data.get("spiff__retry_at") == self.fake_now + 27

                    service_task.internal_data["spiff__retry_at"] = self.fake_now - 1
                    from spiffworkflow_backend.services.workflow_execution_service import WorkflowExecutionServiceError

                    with pytest.raises((UncaughtServiceTaskError, WorkflowExecutionServiceError)):
                        processor.do_engine_steps(save=True)

        assert service_task.state == TaskState.ERROR
        assert service_task.internal_data.get("spiff__retries_attempted") == 3
        assert "spiff__retry_at" not in service_task.internal_data

    def test_service_task_does_not_retry_on_permanent_failure(self, app: Flask, with_db_and_bpmn_file_cleanup: None) -> None:
        processor, _process_instance = self.load_retry_processor()

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

        service_task = self.get_service_task(processor)
        assert service_task.state == TaskState.ERROR
        assert "spiff__retries_attempted" not in service_task.internal_data
