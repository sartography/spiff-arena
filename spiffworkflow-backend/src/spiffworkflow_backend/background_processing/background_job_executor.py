from __future__ import annotations

from typing import cast

from spiffworkflow_backend.background_processing import CELERY_TASK_EVENT_NOTIFIER
from spiffworkflow_backend.background_processing import CELERY_TASK_PROCESS_INSTANCE_RUN
from spiffworkflow_backend.background_processing import CELERY_TASK_PROCESS_INSTANCE_START_FROM_MESSAGE
from spiffworkflow_backend.background_processing import CELERY_TASK_PROCESS_INSTANCE_START_FROM_MODEL
from spiffworkflow_backend.background_processing.background_job import BackgroundJobEnvelope
from spiffworkflow_backend.background_processing.background_job import background_job_context
from spiffworkflow_backend.background_processing.background_job_instrumentation import BackgroundJobInstrumentation
from spiffworkflow_backend.background_processing.celery_tasks.process_instance_task_producer import (
    queue_process_instance_if_appropriate,
)
from spiffworkflow_backend.background_processing.process_instance_operations import notify_process_instance_update
from spiffworkflow_backend.background_processing.process_instance_operations import run_queued_process_instance
from spiffworkflow_backend.background_processing.process_instance_operations import start_process_instance_from_model
from spiffworkflow_backend.background_processing.process_instance_operations import start_reserved_process_from_message
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel


class UnsupportedBackgroundJobError(Exception):
    pass


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
            if result.should_requeue:
                with instrumentation.phase("requeue"):
                    process_instance = ProcessInstanceModel.query.filter_by(id=process_instance_id).one()
                    queue_process_instance_if_appropriate(process_instance, task_guid=result.requeue_task_guid)
        instrumentation.finish_operation(result.outcome.value, process_instance_id=process_instance_id, task_guid=task_guid)
        return result.result()
    except Exception:
        instrumentation.finish_operation("failed", process_instance_id=process_instance_id, task_guid=task_guid)
        raise


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
