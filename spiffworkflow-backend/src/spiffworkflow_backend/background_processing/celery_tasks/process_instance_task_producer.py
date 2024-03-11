import time

import celery
from flask import current_app

from spiffworkflow_backend.background_processing import CELERY_TASK_PROCESS_INSTANCE_RUN
from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.helpers.spiff_enum import ProcessInstanceExecutionMode
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel


def queue_enabled_for_process_model(process_instance: ProcessInstanceModel) -> bool:
    # TODO: check based on the process model itself as well
    return current_app.config["SPIFFWORKFLOW_BACKEND_CELERY_ENABLED"] is True


def should_queue_process_instance(process_instance: ProcessInstanceModel, execution_mode: str | None = None) -> bool:
    # check if the enum value is valid
    if execution_mode:
        ProcessInstanceExecutionMode(execution_mode)

    if execution_mode == ProcessInstanceExecutionMode.synchronous.value:
        return False

    queue_enabled = queue_enabled_for_process_model(process_instance)
    if execution_mode == ProcessInstanceExecutionMode.asynchronous.value and not queue_enabled:
        raise ApiError(
            error_code="async_mode_called_without_celery",
            message="Execution mode asynchronous requested but SPIFFWORKFLOW_BACKEND_CELERY_ENABLED is not set to true.",
            status_code=400,
        )

    if queue_enabled:
        return True
    return False


def queue_future_task_if_appropriate(process_instance: ProcessInstanceModel, eta_in_seconds: float, task_guid: str) -> bool:
    if queue_enabled_for_process_model(process_instance):
        buffer = 1
        countdown = eta_in_seconds - time.time() + buffer
        args_to_celery = {
            "process_instance_id": process_instance.id,
            "task_guid": task_guid,
        }
        # add buffer to countdown to avoid rounding issues and race conditions with spiff. the situation we want to avoid is where
        # we think the timer said to run it at 6:34:11, and we initialize the SpiffWorkflow library,
        # expecting the timer to be ready, but the library considered it ready a little after that time
        # (maybe due to subsecond stuff, maybe because of clock skew within the cluster of computers running spiff)
        # celery_task_process_instance_run.apply_async(kwargs=args_to_celery, countdown=countdown + 1)  # type: ignore

        celery.current_app.send_task(CELERY_TASK_PROCESS_INSTANCE_RUN, kwargs=args_to_celery, countdown=countdown)
        return True

    return False


# if waiting, check all waiting tasks and see if theyt are timers. if they are timers, it's not runnable.
def queue_process_instance_if_appropriate(process_instance: ProcessInstanceModel, execution_mode: str | None = None) -> bool:
    if should_queue_process_instance(process_instance, execution_mode):
        celery.current_app.send_task(CELERY_TASK_PROCESS_INSTANCE_RUN, (process_instance.id,))
        return True
    return False
