from __future__ import annotations

from typing import Any

import pytest
from flask import Flask
from pytest_mock import MockerFixture

from spiffworkflow_backend.background_processing import CELERY_TASK_PROCESS_INSTANCE_RUN
from spiffworkflow_backend.background_processing.background_job import HEADER_PREFIX
from spiffworkflow_backend.background_processing.celery_tasks.process_instance_task import SpiffCeleryWorkerError
from spiffworkflow_backend.background_processing.celery_tasks.process_instance_task import celery_task_process_instance_run
from spiffworkflow_backend.background_processing.process_instance_operations import ProcessInstanceOperationError


def test_run_adapter_maps_delivery_to_shared_executor(app: Flask, mocker: MockerFixture) -> None:
    executor = mocker.patch(
        "spiffworkflow_backend.background_processing.celery_tasks.process_instance_task.execute_background_job",
        return_value={"ok": True, "process_instance_id": 42, "task_guid": "task-1"},
    )
    headers = {
        f"{HEADER_PREFIX}published_at": 10.0,
        f"{HEADER_PREFIX}eligible_at": 12.0,
        f"{HEADER_PREFIX}correlation_id": "correlation-1",
        f"{HEADER_PREFIX}job_id": "job-1",
    }
    task = celery_task_process_instance_run

    with app.app_context():
        task.push_request(id="delivery-1", headers=headers)  # type: ignore[attr-defined]
        try:
            response = task.run(42, "task-1")  # type: ignore[attr-defined]
        finally:
            task.pop_request()  # type: ignore[attr-defined]

    assert response == {"ok": True, "process_instance_id": 42, "task_guid": "task-1"}
    envelope = executor.call_args.args[0]
    assert envelope.job_name == CELERY_TASK_PROCESS_INSTANCE_RUN
    assert envelope.correlation_id == "correlation-1"
    assert envelope.process_instance_id == 42
    assert envelope.task_guid == "task-1"


def test_run_adapter_maps_operation_error_to_celery_error(app: Flask, mocker: MockerFixture) -> None:
    mocker.patch(
        "spiffworkflow_backend.background_processing.celery_tasks.process_instance_task.execute_background_job",
        side_effect=ProcessInstanceOperationError("domain failed"),
    )
    task: Any = celery_task_process_instance_run

    with app.app_context():
        task.push_request(id="delivery-1", headers={})
        try:
            with pytest.raises(SpiffCeleryWorkerError, match="domain failed"):
                task.run(42)
        finally:
            task.pop_request()
