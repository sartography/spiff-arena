from typing import Any

from billiard import current_process  # type: ignore
from celery import shared_task
from flask import current_app

from spiffworkflow_backend.background_processing import CELERY_TASK_PROCESS_INSTANCE_RUN
from spiffworkflow_backend.background_processing import CELERY_TASK_PROCESS_INSTANCE_START_FROM_MESSAGE
from spiffworkflow_backend.background_processing.background_job import BackgroundJobEnvelope
from spiffworkflow_backend.background_processing.background_job import background_job_context
from spiffworkflow_backend.background_processing.background_job_instrumentation import BackgroundJobInstrumentation
from spiffworkflow_backend.background_processing.celery_tasks.process_instance_task_producer import (
    queue_process_instance_if_appropriate,
)
from spiffworkflow_backend.background_processing.process_instance_operations import BackgroundOperationOutcome
from spiffworkflow_backend.background_processing.process_instance_operations import ProcessInstanceOperationError
from spiffworkflow_backend.background_processing.process_instance_operations import run_queued_process_instance
from spiffworkflow_backend.background_processing.process_instance_operations import start_reserved_process_from_message
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService
from spiffworkflow_backend.services.process_model_service import ProcessModelService

TEN_MINUTES = 60 * 10


class SpiffCeleryWorkerError(Exception):
    pass


@shared_task(ignore_result=False, time_limit=TEN_MINUTES, bind=True)
def celery_task_event_notifier_run(
    self: Any,
    updated_process_instance_id: int,
    process_model_identifier: str,
    event_type: str,
) -> dict:
    celery_task_id = self.request.id
    logger_prefix = f"celery_task_event_notifier_run[{celery_task_id}]"
    worker_intro_log_message = f"{logger_prefix}: updated_process_instance_id: {updated_process_instance_id}"
    current_app.logger.info(worker_intro_log_message)

    data = {
        "event": {
            "event_type": event_type,
            "data": {
                "process_instance_id": updated_process_instance_id,
                "process_model_identifier": process_model_identifier,
            },
        }
    }
    try:
        process_model = ProcessModelService.get_process_model(
            current_app.config["SPIFFWORKFLOW_BACKEND_EVENT_NOTIFIER_PROCESS_MODEL"]
        )
        ProcessInstanceService.create_and_run_process_instance(
            process_model=process_model,
            data_to_inject=data,
            persistence_level="none",
        )
    except Exception as exception:
        error_message = (
            f"{logger_prefix}: Error notifying about updating process_instance {updated_process_instance_id}. {str(exception)}"
        )
        raise SpiffCeleryWorkerError(error_message) from exception

    return {**{"ok": True}, **data}


# ignore types so we can use self and get the celery task id from self.request.id.
@shared_task(ignore_result=False, time_limit=TEN_MINUTES, bind=True)
def celery_task_process_instance_run(self, process_instance_id: int, task_guid: str | None = None) -> dict:  # type: ignore
    proc_index = current_process().index
    celery_task_id = self.request.id
    logger_prefix = f"celery_task_process_instance_run[{celery_task_id}]"
    envelope = BackgroundJobEnvelope.from_delivery(
        CELERY_TASK_PROCESS_INSTANCE_RUN,
        {"process_instance_id": process_instance_id, "task_guid": task_guid},
        getattr(self.request, "headers", None),
        delivery_job_id=celery_task_id,
    )
    instrumentation = BackgroundJobInstrumentation(envelope)
    try:
        with background_job_context(envelope):
            result = run_queued_process_instance(process_instance_id, task_guid, instrumentation=instrumentation)
            if result.should_requeue:
                with instrumentation.phase("requeue"):
                    # Delivery remains an adapter concern; the operation only decides whether follow-up work is needed.
                    process_instance = ProcessInstanceModel.query.filter_by(id=process_instance_id).one()
                    queue_process_instance_if_appropriate(process_instance, task_guid=result.requeue_task_guid)
        if result.outcome == BackgroundOperationOutcome.locked:
            exception = result.exception or "unknown locking error"
            instrumentation.finish_operation("locked", process_instance_id=process_instance_id, task_guid=task_guid)
            current_app.logger.info(
                f"{logger_prefix}: Could not run process instance with worker: {current_app.config['PROCESS_UUID']}"
                f" - {proc_index}. Error was: {exception}"
            )
        else:
            instrumentation.finish_operation(result.outcome.value, process_instance_id=process_instance_id, task_guid=task_guid)
        return result.celery_result()
    except ProcessInstanceOperationError as exception:
        instrumentation.finish_operation("failed", process_instance_id=process_instance_id, task_guid=task_guid)
        error_message = f"{logger_prefix}: {str(exception)}"
        raise SpiffCeleryWorkerError(error_message) from exception
    except Exception as exception:
        instrumentation.finish_operation("failed", process_instance_id=process_instance_id, task_guid=task_guid)
        raise SpiffCeleryWorkerError(f"{logger_prefix}: Error adapting background job delivery. {str(exception)}") from exception


@shared_task(ignore_result=False, time_limit=TEN_MINUTES, bind=True)
def celery_task_process_instance_start_from_model(
    self: Any,
    process_model_identifier: str,
    task_guid: str,
    user_id: int,
) -> dict:
    try:
        process_model = ProcessModelService.get_process_model(process_model_identifier)
        user = UserModel.query.filter_by(id=user_id).first()
        if user is None:
            raise SpiffCeleryWorkerError(f"Could not find user with id {user_id}")

        process_instance = ProcessInstanceService.create_and_run_process_instance(
            process_model,
            persistence_level="full",
            data_to_inject={"task_guid": task_guid},
            user=user,
        ).process_instance_model
        return {"ok": True, "process_instance_id": process_instance.id, "task_guid": task_guid}
    except Exception as exception:
        error_message = f"Error in celery_task_process_instance_start_from_model: {str(exception)}"
        raise SpiffCeleryWorkerError(error_message) from exception


@shared_task(ignore_result=False, time_limit=TEN_MINUTES, bind=True)
def celery_task_process_instance_start_from_message(
    self: Any,
    process_instance_id: int,
    message_instance_id: int,
    message_triggerable_process_model_id: int,
) -> dict:
    celery_task_id = self.request.id
    logger_prefix = f"celery_task_process_instance_start_from_message[{celery_task_id}]"
    arguments = {
        "process_instance_id": process_instance_id,
        "message_instance_id": message_instance_id,
        "message_triggerable_process_model_id": message_triggerable_process_model_id,
    }
    envelope = BackgroundJobEnvelope.from_delivery(
        CELERY_TASK_PROCESS_INSTANCE_START_FROM_MESSAGE,
        arguments,
        getattr(self.request, "headers", None),
        delivery_job_id=celery_task_id,
    )
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
        return result.celery_result()
    except ProcessInstanceOperationError as exception:
        instrumentation.finish_operation(
            "failed", process_instance_id=process_instance_id, message_instance_id=message_instance_id
        )
        error_message = f"{logger_prefix}: {str(exception)}"
        raise SpiffCeleryWorkerError(error_message) from exception
