from __future__ import annotations

from types import SimpleNamespace

import pytest
from pytest_mock import MockerFixture

from spiffworkflow_backend.background_processing.process_instance_operations import BackgroundOperationOutcome
from spiffworkflow_backend.background_processing.process_instance_operations import ProcessInstanceOperationError
from spiffworkflow_backend.background_processing.process_instance_operations import run_queued_process_instance
from spiffworkflow_backend.background_processing.process_instance_operations import start_reserved_process_from_message
from spiffworkflow_backend.models.process_instance import ProcessInstanceCannotBeRunError
from spiffworkflow_backend.services.process_instance_queue_service import ProcessInstanceIsAlreadyLockedError
from spiffworkflow_backend.services.workflow_execution_service import TaskRunnability


@pytest.fixture(autouse=True)
def mock_locking_context(mocker: MockerFixture) -> None:
    mocker.patch(
        "spiffworkflow_backend.background_processing.process_instance_operations."
        "ProcessInstanceLockService.set_thread_local_locking_context"
    )


def test_run_operation_skips_missing_process_instance(mocker: MockerFixture) -> None:
    query = mocker.MagicMock()
    mocker.patch(
        "spiffworkflow_backend.background_processing.process_instance_operations.ProcessInstanceModel",
        SimpleNamespace(query=query),
    )
    query.filter_by.return_value.first.return_value = None

    result = run_queued_process_instance(42, "task-1")

    assert result.outcome == BackgroundOperationOutcome.skipped
    assert result.result()["ok"] is True
    assert result.should_requeue is False


def test_run_operation_returns_follow_up_decision_without_publishing(mocker: MockerFixture) -> None:
    process_instance = SimpleNamespace(id=42)
    query = mocker.MagicMock()
    mocker.patch(
        "spiffworkflow_backend.background_processing.process_instance_operations.ProcessInstanceModel",
        SimpleNamespace(query=query),
    )
    query.filter_by.return_value.first.return_value = process_instance
    mocker.patch(
        "spiffworkflow_backend.background_processing.process_instance_operations.ProcessInstanceQueueService.is_enqueued_to_run_in_the_future",
        return_value=False,
    )
    mocker.patch("spiffworkflow_backend.background_processing.process_instance_operations.ProcessInstanceQueueService.dequeued")
    run = mocker.patch(
        "spiffworkflow_backend.background_processing.process_instance_operations.ProcessInstanceService.run_process_instance_with_runtime"
    )
    run.side_effect = [None, (None, TaskRunnability.has_ready_tasks)]

    result = run_queued_process_instance(42)

    assert result.outcome == BackgroundOperationOutcome.success
    assert result.should_requeue is True
    assert result.requeue_task_guid is None


def test_start_message_operation_rolls_back_and_raises_typed_error(mocker: MockerFixture) -> None:
    process_instance = SimpleNamespace(id=42)
    message_instance = SimpleNamespace(id=10)
    trigger = SimpleNamespace(id=11)
    for model, value in (
        ("ProcessInstanceModel", process_instance),
        ("MessageInstanceModel", message_instance),
        ("MessageTriggerableProcessModel", trigger),
    ):
        query = mocker.MagicMock()
        mocker.patch(
            f"spiffworkflow_backend.background_processing.process_instance_operations.{model}",
            SimpleNamespace(query=query),
        )
        query.filter_by.return_value.first.return_value = value
    mocker.patch(
        "spiffworkflow_backend.background_processing.process_instance_operations.MessageService.start_reserved_process_from_message",
        side_effect=ValueError("engine failed"),
    )
    session = mocker.MagicMock()
    mocker.patch("spiffworkflow_backend.background_processing.process_instance_operations.db", SimpleNamespace(session=session))

    with pytest.raises(ProcessInstanceOperationError, match="engine failed"):
        start_reserved_process_from_message(42, 10, 11)

    session.rollback.assert_called_once_with()


def _runnable_process_instance(mocker: MockerFixture) -> None:
    query = mocker.MagicMock()
    mocker.patch(
        "spiffworkflow_backend.background_processing.process_instance_operations.ProcessInstanceModel",
        SimpleNamespace(query=query),
    )
    query.filter_by.return_value.first.return_value = SimpleNamespace(id=42)
    mocker.patch(
        "spiffworkflow_backend.background_processing.process_instance_operations.ProcessInstanceQueueService.is_enqueued_to_run_in_the_future",
        return_value=False,
    )


def _queue_entry(mocker: MockerFixture, entry: SimpleNamespace | None) -> None:
    query = mocker.MagicMock()
    query.filter_by.return_value.first.return_value = entry
    mocker.patch(
        "spiffworkflow_backend.background_processing.process_instance_operations.ProcessInstanceQueueModel",
        SimpleNamespace(query=query),
    )


def test_run_operation_asks_for_a_retry_when_the_process_instance_is_locked(mocker: MockerFixture) -> None:
    _runnable_process_instance(mocker)
    _queue_entry(mocker, SimpleNamespace(locked_by="web:1", locked_at_in_seconds=1000, updated_at_in_seconds=990))
    mocker.patch(
        "spiffworkflow_backend.background_processing.process_instance_operations.ProcessInstanceQueueService.dequeued",
        side_effect=ProcessInstanceIsAlreadyLockedError("locked by web"),
    )

    result = run_queued_process_instance(42, "task-1")

    assert result.outcome == BackgroundOperationOutcome.locked
    assert result.should_requeue is True
    assert result.requeue_task_guid == "task-1"
    assert result.locked_at_in_seconds == 1000


def test_run_operation_reports_no_lock_age_once_the_lock_is_released(mocker: MockerFixture) -> None:
    _runnable_process_instance(mocker)
    _queue_entry(mocker, SimpleNamespace(locked_by=None, locked_at_in_seconds=None, updated_at_in_seconds=990))
    mocker.patch(
        "spiffworkflow_backend.background_processing.process_instance_operations.ProcessInstanceQueueService.dequeued",
        side_effect=ProcessInstanceIsAlreadyLockedError("locked by web"),
    )

    result = run_queued_process_instance(42)

    assert result.should_requeue is True
    assert result.locked_at_in_seconds is None


def test_run_operation_does_not_retry_a_process_instance_that_cannot_run(mocker: MockerFixture) -> None:
    _runnable_process_instance(mocker)
    mocker.patch(
        "spiffworkflow_backend.background_processing.process_instance_operations.ProcessInstanceQueueService.dequeued",
        side_effect=ProcessInstanceCannotBeRunError("terminated"),
    )

    result = run_queued_process_instance(42)

    assert result.outcome == BackgroundOperationOutcome.locked
    assert result.should_requeue is False
