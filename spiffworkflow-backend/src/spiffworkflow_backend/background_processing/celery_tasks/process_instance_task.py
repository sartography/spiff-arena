from typing import Any

from celery import shared_task

from spiffworkflow_backend.background_processing import CELERY_TASK_EVENT_NOTIFIER
from spiffworkflow_backend.background_processing import CELERY_TASK_PROCESS_INSTANCE_RUN
from spiffworkflow_backend.background_processing import CELERY_TASK_PROCESS_INSTANCE_START_FROM_MESSAGE
from spiffworkflow_backend.background_processing import CELERY_TASK_PROCESS_INSTANCE_START_FROM_MODEL
from spiffworkflow_backend.background_processing.background_job import BackgroundJobEnvelope
from spiffworkflow_backend.background_processing.background_job import JobArgument
from spiffworkflow_backend.background_processing.background_job_executor import execute_background_job

TEN_MINUTES = 60 * 10


class SpiffCeleryWorkerError(Exception):
    pass


def _execute(envelope: BackgroundJobEnvelope) -> dict[str, object]:
    try:
        return execute_background_job(envelope)
    except Exception as exception:
        raise SpiffCeleryWorkerError(f"Error executing background job {envelope.job_name}. {str(exception)}") from exception


@shared_task(ignore_result=False, time_limit=TEN_MINUTES, bind=True)
def celery_task_event_notifier_run(
    self: Any,
    updated_process_instance_id: int,
    process_model_identifier: str,
    event_type: str,
) -> dict[str, object]:
    arguments: dict[str, JobArgument] = {
        "updated_process_instance_id": updated_process_instance_id,
        "process_model_identifier": process_model_identifier,
        "event_type": event_type,
    }
    return _execute(
        BackgroundJobEnvelope.from_delivery(
            CELERY_TASK_EVENT_NOTIFIER,
            arguments,
            getattr(self.request, "headers", None),
            delivery_job_id=self.request.id,
            process_instance_id=updated_process_instance_id,
        )
    )


@shared_task(ignore_result=False, time_limit=TEN_MINUTES, bind=True)
def celery_task_process_instance_run(
    self: Any,
    process_instance_id: int,
    task_guid: str | None = None,
) -> dict[str, object]:
    arguments = {"process_instance_id": process_instance_id, "task_guid": task_guid}
    return _execute(
        BackgroundJobEnvelope.from_delivery(
            CELERY_TASK_PROCESS_INSTANCE_RUN,
            arguments,
            getattr(self.request, "headers", None),
            delivery_job_id=self.request.id,
            process_instance_id=process_instance_id,
            task_guid=task_guid,
        )
    )


@shared_task(ignore_result=False, time_limit=TEN_MINUTES, bind=True)
def celery_task_process_instance_start_from_model(
    self: Any,
    process_model_identifier: str,
    task_guid: str,
    user_id: int,
) -> dict[str, object]:
    arguments: dict[str, JobArgument] = {
        "process_model_identifier": process_model_identifier,
        "task_guid": task_guid,
        "user_id": user_id,
    }
    return _execute(
        BackgroundJobEnvelope.from_delivery(
            CELERY_TASK_PROCESS_INSTANCE_START_FROM_MODEL,
            arguments,
            getattr(self.request, "headers", None),
            delivery_job_id=self.request.id,
            task_guid=task_guid,
        )
    )


@shared_task(ignore_result=False, time_limit=TEN_MINUTES, bind=True)
def celery_task_process_instance_start_from_message(
    self: Any,
    process_instance_id: int,
    message_instance_id: int,
    message_triggerable_process_model_id: int,
) -> dict[str, object]:
    arguments = {
        "process_instance_id": process_instance_id,
        "message_instance_id": message_instance_id,
        "message_triggerable_process_model_id": message_triggerable_process_model_id,
    }
    return _execute(
        BackgroundJobEnvelope.from_delivery(
            CELERY_TASK_PROCESS_INSTANCE_START_FROM_MESSAGE,
            arguments,
            getattr(self.request, "headers", None),
            delivery_job_id=self.request.id,
            process_instance_id=process_instance_id,
        )
    )
