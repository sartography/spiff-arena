from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from flask import Flask
from pytest_mock import MockerFixture

from spiffworkflow_backend.background_processing import CELERY_TASK_EVENT_NOTIFIER
from spiffworkflow_backend.background_processing import CELERY_TASK_PROCESS_INSTANCE_RUN
from spiffworkflow_backend.background_processing import CELERY_TASK_PROCESS_INSTANCE_START_FROM_MESSAGE
from spiffworkflow_backend.background_processing import CELERY_TASK_PROCESS_INSTANCE_START_FROM_MODEL
from spiffworkflow_backend.background_processing.background_job import BackgroundJobEnvelope
from spiffworkflow_backend.background_processing.background_job_executor import LOCKED_RUN_MAX_RETRIES
from spiffworkflow_backend.background_processing.background_job_executor import UnsupportedBackgroundJobError
from spiffworkflow_backend.background_processing.background_job_executor import execute_background_job
from spiffworkflow_backend.background_processing.background_job_executor import locked_run_retry_delay
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


NOW = 10_000.0


def _locked_run(mocker: MockerFixture, locked_at_in_seconds: int | None = None) -> tuple[MagicMock, MagicMock]:
    mocker.patch(
        "spiffworkflow_backend.background_processing.background_job_executor.run_queued_process_instance",
        return_value=RunQueuedProcessInstanceResult(
            BackgroundOperationOutcome.locked,
            42,
            "task-1",
            exception="locked by web",
            should_requeue=True,
            requeue_task_guid="task-1",
            locked_at_in_seconds=locked_at_in_seconds,
        ),
    )
    mocker.patch("spiffworkflow_backend.background_processing.background_job_executor.time.time", return_value=NOW)
    retry = mocker.patch(
        "spiffworkflow_backend.background_processing.background_job_executor.queue_locked_process_instance_run_retry"
    )
    queue = mocker.patch(
        "spiffworkflow_backend.background_processing.background_job_executor.queue_process_instance_if_appropriate"
    )
    return retry, queue


def test_locked_run_is_retried_with_backoff(mocker: MockerFixture, app: Flask) -> None:
    retry, queue = _locked_run(mocker)
    job = BackgroundJobEnvelope.create(
        CELERY_TASK_PROCESS_INSTANCE_RUN, {"process_instance_id": 42, "task_guid": "task-1"}, now=10.0, lock_retry_count=2
    )

    with app.app_context():
        result = execute_background_job(job)

    assert result["ok"] is False
    retry.assert_called_once_with(42, "task-1", lock_retry_count=3, countdown=4.0)
    queue.assert_not_called()


def test_locked_run_gives_up_after_the_last_retry(mocker: MockerFixture, app: Flask) -> None:
    retry, queue = _locked_run(mocker)
    job = BackgroundJobEnvelope.create(
        CELERY_TASK_PROCESS_INSTANCE_RUN,
        {"process_instance_id": 42, "task_guid": "task-1"},
        now=10.0,
        lock_retry_count=LOCKED_RUN_MAX_RETRIES,
    )

    with app.app_context():
        execute_background_job(job)

    retry.assert_not_called()
    queue.assert_not_called()


def test_locked_run_retry_delays_back_off_to_a_minute() -> None:
    delays = [locked_run_retry_delay(count) for count in range(1, LOCKED_RUN_MAX_RETRIES + 1)]

    assert delays[:4] == [1.0, 2.0, 4.0, 8.0]
    assert max(delays) == 60.0


def test_locked_run_retries_while_the_lock_it_saw_is_young(mocker: MockerFixture, app: Flask) -> None:
    retry, _queue = _locked_run(mocker, locked_at_in_seconds=int(NOW) - 10)
    job = BackgroundJobEnvelope.create(CELERY_TASK_PROCESS_INSTANCE_RUN, {"process_instance_id": 42}, now=NOW)

    with app.app_context():
        execute_background_job(job)

    retry.assert_called_once_with(42, "task-1", lock_retry_count=1, countdown=1.0)


def test_locked_run_does_not_retry_into_stale_lock_removal(mocker: MockerFixture, app: Flask) -> None:
    # remove_stale_locks releases a lock by age even while its holder still runs; a retry
    # landing after that could run the instance alongside the holder.
    lock_duration = app.config["MAX_INSTANCE_LOCK_DURATION_IN_SECONDS"]
    retry, _queue = _locked_run(mocker, locked_at_in_seconds=int(NOW) - lock_duration + 5)
    job = BackgroundJobEnvelope.create(CELERY_TASK_PROCESS_INSTANCE_RUN, {"process_instance_id": 42}, now=NOW)

    with app.app_context():
        execute_background_job(job)

    retry.assert_not_called()
