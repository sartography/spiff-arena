import time

from billiard import current_process  # type: ignore
from celery import shared_task
from flask import current_app

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.future_task import FutureTaskModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.services.process_instance_lock_service import ProcessInstanceLockService
from spiffworkflow_backend.services.process_instance_queue_service import ProcessInstanceIsAlreadyLockedError
from spiffworkflow_backend.services.process_instance_queue_service import ProcessInstanceQueueService
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService
from spiffworkflow_backend.services.workflow_execution_service import TaskRunnability


def queue_enabled_for_process_model(process_instance: ProcessInstanceModel) -> bool:
    # TODO: check based on the process model itself as well
    return current_app.config["SPIFFWORKFLOW_BACKEND_CELERY_ENABLED"] is True


def queue_future_task_if_appropriate(process_instance: ProcessInstanceModel, eta_in_seconds: float, task_guid: str) -> bool:
    if queue_enabled_for_process_model(process_instance):
        countdown = eta_in_seconds - time.time()
        args_to_celery = {"process_instance_id": process_instance.id, "task_guid": task_guid}
        # add buffer to countdown to avoid rounding issues and race conditions with spiff. the situation we want to avoid is where
        # we think the timer said to run it at 6:34:11, and we initialize the SpiffWorkflow library,
        # expecting the timer to be ready, but the library considered it ready a little after that time
        # (maybe due to subsecond stuff, maybe because of clock skew within the cluster of computers running spiff)
        celery_task_process_instance_run.apply_async(kwargs=args_to_celery, countdown=countdown + 1)  # type: ignore
        return True

    return False


# if waiting, check all waiting tasks and see if theyt are timers. if they are timers, it's not runnable.
def queue_process_instance_if_appropriate(process_instance: ProcessInstanceModel) -> bool:
    if queue_enabled_for_process_model(process_instance):
        celery_task_process_instance_run.delay(process_instance.id)  # type: ignore
        return True

    return False


ten_minutes = 60 * 10


@shared_task(ignore_result=False, time_limit=ten_minutes)
def celery_task_process_instance_run(process_instance_id: int, task_guid: str | None = None) -> None:
    proc_index = current_process().index
    ProcessInstanceLockService.set_thread_local_locking_context("celery:worker", additional_processing_identifier=proc_index)
    process_instance = ProcessInstanceModel.query.filter_by(id=process_instance_id).first()
    try:
        with ProcessInstanceQueueService.dequeued(process_instance, additional_processing_identifier=proc_index):
            ProcessInstanceService.run_process_instance_with_processor(
                process_instance, execution_strategy_name="run_current_ready_tasks", additional_processing_identifier=proc_index
            )
            processor, task_runnability = ProcessInstanceService.run_process_instance_with_processor(
                process_instance,
                execution_strategy_name="queue_instructions_for_end_user",
                additional_processing_identifier=proc_index,
            )
            if task_guid is not None:
                future_task = FutureTaskModel.query.filter_by(completed=False, guid=task_guid).first()
                if future_task is not None:
                    future_task.completed = True
                    db.session.add(future_task)
                    db.session.commit()
            if task_runnability == TaskRunnability.has_ready_tasks:
                queue_process_instance_if_appropriate(process_instance)
    except ProcessInstanceIsAlreadyLockedError:
        pass
    except Exception as e:
        db.session.rollback()  # in case the above left the database with a bad transaction
        error_message = (
            f"Error running process_instance {process_instance.id}" + f"({process_instance.process_model_identifier}). {str(e)}"
        )
        current_app.logger.error(error_message)
        db.session.add(process_instance)
        db.session.commit()
        raise e
