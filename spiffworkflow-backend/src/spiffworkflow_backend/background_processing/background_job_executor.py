from __future__ import annotations

import time
from typing import cast

from flask import current_app

from spiffworkflow_backend.background_processing import CELERY_TASK_EVENT_NOTIFIER
from spiffworkflow_backend.background_processing import CELERY_TASK_PROCESS_INSTANCE_RUN
from spiffworkflow_backend.background_processing import CELERY_TASK_PROCESS_INSTANCE_START_FROM_MESSAGE
from spiffworkflow_backend.background_processing import CELERY_TASK_PROCESS_INSTANCE_START_FROM_MODEL
from spiffworkflow_backend.background_processing.background_job import BackgroundJobEnvelope
from spiffworkflow_backend.background_processing.background_job import background_job_context
from spiffworkflow_backend.background_processing.background_job_instrumentation import BackgroundJobInstrumentation
from spiffworkflow_backend.background_processing.celery_tasks.process_instance_task_producer import (
    queue_locked_process_instance_run_retry,
)
from spiffworkflow_backend.background_processing.celery_tasks.process_instance_task_producer import (
    queue_process_instance_if_appropriate,
)
from spiffworkflow_backend.background_processing.process_instance_operations import BackgroundOperationOutcome
from spiffworkflow_backend.background_processing.process_instance_operations import notify_process_instance_update
from spiffworkflow_backend.background_processing.process_instance_operations import run_queued_process_instance
from spiffworkflow_backend.background_processing.process_instance_operations import start_process_instance_from_model
from spiffworkflow_backend.background_processing.process_instance_operations import start_reserved_process_from_message
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel

# A run that finds its process instance locked retries with backoff (1, 2, 4 ... 60 seconds), but only
# while the lock it saw is younger than MAX_INSTANCE_LOCK_DURATION_IN_SECONDS. remove_stale_locks
# releases older locks by age alone, even if their holder is still running, so a retry after that point
# could run the instance alongside it. A holder that is a queued run requeues itself when it leaves READY
# tasks behind.
LOCKED_RUN_MAX_RETRIES = 15
LOCKED_RUN_MAX_RETRY_DELAY_IN_SECONDS = 60
# Room for clock skew between hosts and for the broker delivering a countdown late.
LOCKED_RUN_STALE_LOCK_MARGIN_IN_SECONDS = 10


class UnsupportedBackgroundJobError(Exception):
    pass


def locked_run_retry_delay(lock_retry_count: int) -> float:
    return float(min(2 ** max(lock_retry_count - 1, 0), LOCKED_RUN_MAX_RETRY_DELAY_IN_SECONDS))


# Order of operations:
#   src/spiffworkflow_backend/background_processing/celery_tasks/process_instance_task_producer.py
#   src/spiffworkflow_backend/background_processing/celery_tasks/process_instance_task.py
#   src/spiffworkflow_backend/background_processing/background_job_executor.py # this file :D
#   src/spiffworkflow_backend/background_processing/process_instance_operations.py
def execute_background_job(envelope: BackgroundJobEnvelope) -> dict[str, object]:
    arguments = envelope.arguments
    if envelope.job_name == CELERY_TASK_PROCESS_INSTANCE_RUN:
        return _execute_process_instance_run(
            envelope,
            cast(int, arguments["process_instance_id"]),
            cast(str | None, arguments.get("task_guid")),
        )
    if envelope.job_name == CELERY_TASK_PROCESS_INSTANCE_START_FROM_MESSAGE:
        return _execute_process_instance_start_from_message(
            envelope,
            cast(int, arguments["process_instance_id"]),
            cast(int, arguments["message_instance_id"]),
            cast(int, arguments["message_triggerable_process_model_id"]),
        )
    with background_job_context(envelope):
        if envelope.job_name == CELERY_TASK_EVENT_NOTIFIER:
            return notify_process_instance_update(
                cast(int, arguments["updated_process_instance_id"]),
                cast(str, arguments["process_model_identifier"]),
                cast(str, arguments["event_type"]),
            )
        if envelope.job_name == CELERY_TASK_PROCESS_INSTANCE_START_FROM_MODEL:
            return start_process_instance_from_model(
                cast(str, arguments["process_model_identifier"]),
                cast(str, arguments["task_guid"]),
                cast(int, arguments["user_id"]),
            )
    raise UnsupportedBackgroundJobError(f"Unsupported background job: {envelope.job_name}")


def _execute_process_instance_run(
    envelope: BackgroundJobEnvelope,
    process_instance_id: int,
    task_guid: str | None,
) -> dict[str, object]:
    instrumentation = BackgroundJobInstrumentation(envelope)
    try:
        with background_job_context(envelope):
            result = run_queued_process_instance(process_instance_id, task_guid, instrumentation=instrumentation)
            if result.should_requeue and result.outcome == BackgroundOperationOutcome.locked:
                with instrumentation.phase("requeue"):
                    _retry_locked_run(envelope, process_instance_id, result.requeue_task_guid, result.locked_at_in_seconds)
            elif result.should_requeue:
                with instrumentation.phase("requeue"):
                    process_instance = ProcessInstanceModel.query.filter_by(id=process_instance_id).one()
                    queue_process_instance_if_appropriate(process_instance, task_guid=result.requeue_task_guid)
        instrumentation.finish_operation(result.outcome.value, process_instance_id=process_instance_id, task_guid=task_guid)
        return result.result()
    except Exception:
        instrumentation.finish_operation("failed", process_instance_id=process_instance_id, task_guid=task_guid)
        raise


def _retry_locked_run(
    envelope: BackgroundJobEnvelope,
    process_instance_id: int,
    task_guid: str | None,
    locked_at_in_seconds: int | None,
) -> None:
    lock_retry_count = envelope.lock_retry_count + 1
    countdown = locked_run_retry_delay(lock_retry_count)
    if lock_retry_count > LOCKED_RUN_MAX_RETRIES:
        current_app.logger.error(
            f"Process instance ({process_instance_id}) stayed locked through {LOCKED_RUN_MAX_RETRIES} run retries; "
            "giving up on this run. Its ready tasks wait until something else queues it."
        )
        return
    if locked_at_in_seconds is not None:
        lock_expires_at = locked_at_in_seconds + current_app.config["MAX_INSTANCE_LOCK_DURATION_IN_SECONDS"]
        if time.time() + countdown + LOCKED_RUN_STALE_LOCK_MARGIN_IN_SECONDS >= lock_expires_at:
            current_app.logger.warning(
                f"Process instance ({process_instance_id}) has been locked since {locked_at_in_seconds}; not retrying "
                "its run past the point where that lock can be removed as stale while its holder may still run."
            )
            return
    queue_locked_process_instance_run_retry(
        process_instance_id,
        task_guid,
        lock_retry_count=lock_retry_count,
        countdown=countdown,
    )


def _execute_process_instance_start_from_message(
    envelope: BackgroundJobEnvelope,
    process_instance_id: int,
    message_instance_id: int,
    message_triggerable_process_model_id: int,
) -> dict[str, object]:
    instrumentation = BackgroundJobInstrumentation(envelope)
    try:
        with background_job_context(envelope):
            result = start_reserved_process_from_message(
                process_instance_id,
                message_instance_id,
                message_triggerable_process_model_id,
                instrumentation=instrumentation,
            )
        instrumentation.finish_operation(
            result.outcome.value,
            process_instance_id=process_instance_id,
            message_instance_id=message_instance_id,
            receiver_message_instance_id=result.receiver_message_instance_id,
        )
        return result.result()
    except Exception:
        instrumentation.finish_operation(
            "failed", process_instance_id=process_instance_id, message_instance_id=message_instance_id
        )
        raise
