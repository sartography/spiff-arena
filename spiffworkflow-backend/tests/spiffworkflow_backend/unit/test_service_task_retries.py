import json
from typing import Any
from typing import Protocol
from typing import cast
from unittest.mock import patch

import pytest
from flask.app import Flask
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore
from SpiffWorkflow.util.task import TaskState  # type: ignore

from spiffworkflow_backend.background_processing.celery_tasks.process_instance_task import celery_task_process_instance_run
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.future_task import FutureTaskModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance_event import ProcessInstanceEventModel
from spiffworkflow_backend.models.process_instance_event import ProcessInstanceEventType
from spiffworkflow_backend.models.task import TaskModel
from spiffworkflow_backend.services.process_instance_runtime import ProcessInstanceRuntime
from spiffworkflow_backend.services.service_task_delegate import UncaughtServiceTaskError
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class SupportsCeleryTaskRun(Protocol):
    def run(self, process_instance_id: int, task_guid: str | None = None) -> dict[str, Any]: ...


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

    def load_retry_runtime(self, bpmn_file_name: str = "retries.bpmn") -> tuple[ProcessInstanceRuntime, ProcessInstanceModel]:
        process_model = load_test_spec(
            process_model_id="test_group/retries",
            bpmn_file_name=bpmn_file_name,
            process_model_source_directory="retries",
        )
        process_instance = self.create_process_instance_from_process_model(process_model=process_model)
        runtime = ProcessInstanceRuntime(process_instance)
        runtime.bpmn_process_instance.data["process_instance_id"] = process_instance.id
        return runtime, process_instance

    def get_service_task(self, runtime: ProcessInstanceRuntime) -> SpiffTask:
        tasks = runtime.bpmn_process_instance.get_tasks()
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
        runtime, _process_instance = self.load_retry_runtime()
        service_task_specs = self.service_task_specs_in(runtime.serialize())

        assert len(service_task_specs) == 1
        assert service_task_specs[0]["retries"] == 3
        assert "retry_backoff_base" not in service_task_specs[0]

    def test_service_task_retry_backoff_base_can_be_overridden_in_bpmn(
        self, app: Flask, with_db_and_bpmn_file_cleanup: None
    ) -> None:
        runtime, process_instance = self.load_retry_runtime("retries_backoff_override.bpmn")

        service_task_specs = self.service_task_specs_in(runtime.serialize())
        assert len(service_task_specs) == 1
        assert service_task_specs[0]["retry_backoff_base"] == 2

        with patch("requests.get") as mock_get:
            self.transient_failure_response(mock_get)
            custom_service_task_time, workflow_execution_service_time = self.patch_retry_time()
            with custom_service_task_time, workflow_execution_service_time:
                with patch("celery.current_app.send_task"):
                    with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_CELERY_ENABLED", True):
                        runtime.do_engine_steps(save=True)

        service_task = self.get_service_task(runtime)
        assert service_task.internal_data.get("spiff__retries_attempted") == 0
        assert service_task.internal_data.get("spiff__retry_at") == self.fake_now + 2
        assert process_instance.spiffworkflow_fully_initialized()

    def test_service_task_retries_on_failure(self, app: Flask, with_db_and_bpmn_file_cleanup: None) -> None:
        runtime, _process_instance = self.load_retry_runtime()

        with patch("requests.get") as mock_get, patch("spiffworkflow_backend.services.custom_service_task.logger") as logger:
            self.transient_failure_response(mock_get)
            custom_service_task_time, workflow_execution_service_time = self.patch_retry_time()
            with custom_service_task_time, workflow_execution_service_time:
                with patch("celery.current_app.send_task"):
                    with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_CELERY_ENABLED", True):
                        runtime.do_engine_steps(save=True)

        service_task = self.get_service_task(runtime)
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
        assert logger.warning.call_count == 1
        assert "failed and will retry" in logger.warning.call_args.args[0]
        assert logger.warning.call_args.args[2] == _process_instance.id
        assert logger.exception.call_count == 0

    def test_service_task_retries_on_upstream_failure_in_successful_proxy_response(
        self, app: Flask, with_db_and_bpmn_file_cleanup: None
    ) -> None:
        runtime, _process_instance = self.load_retry_runtime()

        with patch("requests.post") as mock_post:
            self.proxy_success_with_upstream_failure_response(mock_post.return_value)
            custom_service_task_time, workflow_execution_service_time = self.patch_retry_time()
            with custom_service_task_time, workflow_execution_service_time:
                with (
                    patch("celery.current_app.send_task"),
                    patch("spiffworkflow_backend.services.service_task_delegate.http_connector.does", return_value=False),
                ):
                    with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_CELERY_ENABLED", True):
                        runtime.do_engine_steps(save=True)

        service_task = self.get_service_task(runtime)
        assert service_task.state == TaskState.STARTED
        assert service_task.internal_data.get("spiff__retries_attempted") == 0
        assert service_task.internal_data.get("spiff__retry_at") == self.fake_now + 3

        future_task = FutureTaskModel.query.filter_by(guid=str(service_task.id)).first()
        assert future_task is not None
        assert future_task.completed is False

    def test_builtin_http_connector_retries_downstream_debug_endpoint_500(
        self, app: Flask, with_db_and_bpmn_file_cleanup: None
    ) -> None:
        runtime, process_instance = self.load_retry_runtime("builtin_http_debug_error.bpmn")

        custom_service_task_time, workflow_execution_service_time = self.patch_retry_time()
        with custom_service_task_time, workflow_execution_service_time:
            with patch("celery.current_app.send_task"):
                with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_CELERY_ENABLED", True):
                    runtime.do_engine_steps(save=True)

        service_task = self.get_service_task(runtime)
        assert service_task.state == TaskState.STARTED
        assert service_task.internal_data.get("spiff__retries_attempted") == 0
        assert service_task.internal_data.get("spiff__retry_at") == self.fake_now + 3

        future_task = FutureTaskModel.query.filter_by(guid=str(service_task.id)).first()
        assert future_task is not None
        assert future_task.completed is False
        assert process_instance.spiffworkflow_fully_initialized()

    def test_service_task_retries_when_retry_at_is_due(self, app: Flask, with_db_and_bpmn_file_cleanup: None) -> None:
        runtime, process_instance = self.load_retry_runtime()

        with patch("requests.get") as mock_get:
            self.transient_failure_response(mock_get)
            custom_service_task_time, workflow_execution_service_time = self.patch_retry_time()
            with custom_service_task_time, workflow_execution_service_time:
                with patch("celery.current_app.send_task"):
                    with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_CELERY_ENABLED", True):
                        runtime.do_engine_steps(save=True)

                    assert process_instance.spiffworkflow_fully_initialized()

                    db.session.expire_all()
                    reloaded_process_instance = ProcessInstanceModel.query.filter_by(id=process_instance.id).one()
                    runtime = ProcessInstanceRuntime(reloaded_process_instance)
                    service_task = self.get_service_task(runtime)
                    assert service_task.state == TaskState.STARTED
                    assert service_task.task_spec.retries == 3
                    assert service_task.task_spec.retry_backoff_base is None
                    assert service_task.internal_data.get("spiff__retries_attempted") == 0

                    service_task.internal_data["spiff__retry_at"] = self.fake_now - 1

                    with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_CELERY_ENABLED", True):
                        runtime.do_engine_steps(save=True)

        assert mock_get.call_count == 2
        assert service_task.state == TaskState.STARTED
        assert service_task.internal_data.get("spiff__retries_attempted") == 1
        assert service_task.internal_data.get("spiff__retry_at") == self.fake_now + 9

    def test_service_task_worker_does_not_immediately_requeue_rescheduled_retry(
        self, app: Flask, with_db_and_bpmn_file_cleanup: None
    ) -> None:
        runtime, process_instance = self.load_retry_runtime()

        with patch("requests.get") as mock_get:
            self.transient_failure_response(mock_get)
            custom_service_task_time, workflow_execution_service_time = self.patch_retry_time()
            with custom_service_task_time, workflow_execution_service_time:
                with patch("celery.current_app.send_task"):
                    with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_CELERY_ENABLED", True):
                        runtime.do_engine_steps(save=True)

            service_task = self.get_service_task(runtime)
            assert service_task.internal_data.get("spiff__retry_at") == self.fake_now + 3

            db.session.expire_all()
            reloaded_process_instance = ProcessInstanceModel.query.filter_by(id=process_instance.id).one()

            with (
                patch(
                    "spiffworkflow_backend.background_processing.celery_tasks.process_instance_task.current_process"
                ) as current_process,
                patch(
                    "spiffworkflow_backend.background_processing.celery_tasks.process_instance_task_producer.time.time",
                    return_value=self.fake_now + 3,
                ),
                patch("spiffworkflow_backend.services.custom_service_task.time.time", return_value=self.fake_now + 3),
                patch("spiffworkflow_backend.services.workflow_execution_service.time.time", return_value=self.fake_now + 3),
                patch("celery.current_app.send_task") as send_task,
            ):
                current_process.return_value.index = 0
                with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_CELERY_ENABLED", True):
                    cast(SupportsCeleryTaskRun, celery_task_process_instance_run).run(
                        reloaded_process_instance.id, str(service_task.id)
                    )

        assert mock_get.call_count == 2

        reloaded_runtime = ProcessInstanceRuntime(ProcessInstanceModel.query.filter_by(id=process_instance.id).one())
        reloaded_service_task = self.get_service_task(reloaded_runtime)
        assert reloaded_service_task.state == TaskState.STARTED
        assert reloaded_service_task.internal_data.get("spiff__retries_attempted") == 1
        assert reloaded_service_task.internal_data.get("spiff__retry_at") == self.fake_now + 12

        assert send_task.call_count == 1
        assert send_task.call_args.kwargs["countdown"] == 10

    def test_service_task_fails_after_exhausting_retries(self, app: Flask, with_db_and_bpmn_file_cleanup: None) -> None:
        runtime, _process_instance = self.load_retry_runtime()

        with patch("requests.get") as mock_get:
            self.transient_failure_response(mock_get)
            custom_service_task_time, workflow_execution_service_time = self.patch_retry_time()
            with custom_service_task_time, workflow_execution_service_time:
                with patch("celery.current_app.send_task"):
                    with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_CELERY_ENABLED", True):
                        runtime.do_engine_steps(save=True)

                    service_task = self.get_service_task(runtime)
                    assert service_task.internal_data.get("spiff__retries_attempted") == 0
                    assert service_task.internal_data.get("spiff__retry_at") == self.fake_now + 3

                    service_task.internal_data["spiff__retry_at"] = self.fake_now - 1
                    with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_CELERY_ENABLED", True):
                        runtime.do_engine_steps(save=True)
                    assert service_task.internal_data.get("spiff__retries_attempted") == 1
                    assert service_task.internal_data.get("spiff__retry_at") == self.fake_now + 9

                    service_task.internal_data["spiff__retry_at"] = self.fake_now - 1
                    with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_CELERY_ENABLED", True):
                        runtime.do_engine_steps(save=True)
                    assert service_task.internal_data.get("spiff__retries_attempted") == 2
                    assert service_task.internal_data.get("spiff__retry_at") == self.fake_now + 27

                    service_task.internal_data["spiff__retry_at"] = self.fake_now - 1
                    from spiffworkflow_backend.services.workflow_execution_service import WorkflowExecutionServiceError

                    with pytest.raises((UncaughtServiceTaskError, WorkflowExecutionServiceError)):
                        runtime.do_engine_steps(save=True)

        assert service_task.state == TaskState.ERROR
        assert service_task.internal_data.get("spiff__retries_attempted") == 3
        assert "spiff__retry_at" not in service_task.internal_data

    def test_service_task_does_not_retry_on_permanent_failure(self, app: Flask, with_db_and_bpmn_file_cleanup: None) -> None:
        runtime, _process_instance = self.load_retry_runtime()

        with patch("requests.get") as mock_get, patch("spiffworkflow_backend.services.custom_service_task.logger") as logger:
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
                runtime.do_engine_steps(save=True)

        service_task = self.get_service_task(runtime)
        assert service_task.state == TaskState.ERROR
        assert "spiff__retries_attempted" not in service_task.internal_data
        assert logger.error.call_count == 1
        assert "failed and will not retry" in logger.error.call_args.args[0]
        assert logger.error.call_args.args[2] == _process_instance.id
        assert logger.error.call_args.args[5] == "not_retryable"
        assert logger.exception.call_count == 0
