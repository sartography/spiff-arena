from __future__ import annotations

from typing import Any

import pytest
from flask import Flask
from pytest_mock import MockerFixture

from spiffworkflow_backend.background_processing import CELERY_TASK_PROCESS_INSTANCE_RUN
from spiffworkflow_backend.background_processing.background_job import HEADER_PREFIX
from spiffworkflow_backend.background_processing.celery_tasks.process_instance_task import SpiffCeleryWorkerError
from spiffworkflow_backend.background_processing.celery_tasks.process_instance_task import celery_task_process_instance_run
from spiffworkflow_backend.background_processing.process_instance_operations import BackgroundOperationOutcome
from spiffworkflow_backend.background_processing.process_instance_operations import ProcessInstanceOperationError
from spiffworkflow_backend.background_processing.process_instance_operations import RunQueuedProcessInstanceResult


def test_run_adapter_maps_delivery_metadata_and_operation_result(
    app: Flask,
    mocker: MockerFixture,
) -> None:
    operation = mocker.patch(
        "spiffworkflow_backend.background_processing.celery_tasks.process_instance_task.run_queued_process_instance",
        return_value=RunQueuedProcessInstanceResult(BackgroundOperationOutcome.success, 42, "task-1"),
    )
    mocker.patch(
        "spiffworkflow_backend.background_processing.celery_tasks.process_instance_task.current_process",
        return_value=mocker.Mock(index=1),
    )
    headers = {
        f"{HEADER_PREFIX}envelope_version": 1,
        f"{HEADER_PREFIX}published_at": 10.0,
        f"{HEADER_PREFIX}eligible_at": 12.0,
        f"{HEADER_PREFIX}correlation_id": "correlation-1",
        f"{HEADER_PREFIX}job_id": "job-1",
        f"{HEADER_PREFIX}original_job_id": "original-1",
        f"{HEADER_PREFIX}attempt": 2,
    }
    task = celery_task_process_instance_run

    with app.app_context():
        task.push_request(id="delivery-1", headers=headers)  # type: ignore[attr-defined]
        try:
            response = task.run(42, "task-1")  # type: ignore[attr-defined]
        finally:
            task.pop_request()  # type: ignore[attr-defined]

    assert response == {"ok": True, "process_instance_id": 42, "task_guid": "task-1"}
    instrumentation = operation.call_args.kwargs["instrumentation"]
    assert instrumentation.envelope.job_name == CELERY_TASK_PROCESS_INSTANCE_RUN
    assert instrumentation.envelope.correlation_id == "correlation-1"
    assert instrumentation.envelope.original_job_id == "original-1"
    assert instrumentation.envelope.attempt == 2


def test_run_adapter_maps_operation_error_to_celery_error(app: Flask, mocker: MockerFixture) -> None:
    mocker.patch(
        "spiffworkflow_backend.background_processing.celery_tasks.process_instance_task.run_queued_process_instance",
        side_effect=ProcessInstanceOperationError("domain failed"),
    )
    mocker.patch(
        "spiffworkflow_backend.background_processing.celery_tasks.process_instance_task.current_process",
        return_value=mocker.Mock(index=1),
    )
    task: Any = celery_task_process_instance_run

    with app.app_context():
        task.push_request(id="delivery-1", headers={})
        try:
            with pytest.raises(SpiffCeleryWorkerError, match="domain failed"):
                task.run(42)
        finally:
            task.pop_request()
