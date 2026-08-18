from __future__ import annotations

from types import SimpleNamespace

import pytest
from pytest_mock import MockerFixture

from spiffworkflow_backend.background_processing import CELERY_TASK_EVENT_NOTIFIER
from spiffworkflow_backend.background_processing import CELERY_TASK_PROCESS_INSTANCE_RUN
from spiffworkflow_backend.background_processing import CELERY_TASK_PROCESS_INSTANCE_START_FROM_MESSAGE
from spiffworkflow_backend.background_processing import CELERY_TASK_PROCESS_INSTANCE_START_FROM_MODEL
from spiffworkflow_backend.background_processing.background_job import BackgroundJobEnvelope
from spiffworkflow_backend.background_processing.background_job_executor import UnsupportedBackgroundJobError
from spiffworkflow_backend.background_processing.background_job_executor import execute_background_job
from spiffworkflow_backend.background_processing.process_instance_operations import BackgroundOperationOutcome
from spiffworkflow_backend.background_processing.process_instance_operations import RunQueuedProcessInstanceResult
from spiffworkflow_backend.background_processing.process_instance_operations import StartReservedProcessFromMessageResult


def envelope(job_name: str, arguments: dict[str, str | int | None]) -> BackgroundJobEnvelope:
    return BackgroundJobEnvelope.create(job_name, arguments, now=10.0)


def test_executes_process_instance_run_and_requeues(mocker: MockerFixture) -> None:
    operation = mocker.patch(
        "spiffworkflow_backend.background_processing.background_job_executor.run_queued_process_instance",
        return_value=RunQueuedProcessInstanceResult(
            BackgroundOperationOutcome.success,
            42,
            "task-1",
            should_requeue=True,
            requeue_task_guid="task-2",
        ),
    )
    process_instance = SimpleNamespace(id=42)
    process_model = mocker.patch("spiffworkflow_backend.background_processing.background_job_executor.ProcessInstanceModel")
    process_model.query.filter_by.return_value.one.return_value = process_instance
    queue = mocker.patch(
        "spiffworkflow_backend.background_processing.background_job_executor.queue_process_instance_if_appropriate"
    )

    result = execute_background_job(
        envelope(CELERY_TASK_PROCESS_INSTANCE_RUN, {"process_instance_id": 42, "task_guid": "task-1"})
    )

    assert result == {"ok": True, "process_instance_id": 42, "task_guid": "task-1"}
    assert operation.call_args.args == (42, "task-1")
    queue.assert_called_once_with(process_instance, task_guid="task-2")


def test_executes_message_start(mocker: MockerFixture) -> None:
    operation = mocker.patch(
        "spiffworkflow_backend.background_processing.background_job_executor.start_reserved_process_from_message",
        return_value=StartReservedProcessFromMessageResult(BackgroundOperationOutcome.success, 42, 10, 11),
    )

    result = execute_background_job(
        envelope(
            CELERY_TASK_PROCESS_INSTANCE_START_FROM_MESSAGE,
            {"process_instance_id": 42, "message_instance_id": 10, "message_triggerable_process_model_id": 20},
        )
    )

    assert result == {"ok": True, "process_instance_id": 42, "message_instance_id": 10, "receiver_message_instance_id": 11}
    assert operation.call_args.args == (42, 10, 20)


@pytest.mark.parametrize(
    ("job_name", "arguments", "operation_name"),
    [
        (
            CELERY_TASK_EVENT_NOTIFIER,
            {"updated_process_instance_id": 42, "process_model_identifier": "group/model", "event_type": "complete"},
            "notify_process_instance_update",
        ),
        (
            CELERY_TASK_PROCESS_INSTANCE_START_FROM_MODEL,
            {"process_model_identifier": "group/model", "task_guid": "task-1", "user_id": 7},
            "start_process_instance_from_model",
        ),
    ],
)
def test_executes_other_published_job_types(
    mocker: MockerFixture,
    job_name: str,
    arguments: dict[str, str | int | None],
    operation_name: str,
) -> None:
    operation = mocker.patch(
        f"spiffworkflow_backend.background_processing.background_job_executor.{operation_name}",
        return_value={"ok": True},
    )

    assert execute_background_job(envelope(job_name, arguments)) == {"ok": True}
    operation.assert_called_once()


def test_rejects_unknown_job_name() -> None:
    with pytest.raises(UnsupportedBackgroundJobError, match="unknown"):
        execute_background_job(envelope("unknown", {}))
