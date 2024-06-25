from billiard import current_process  # type: ignore
from celery import shared_task
from flask import current_app

from spiffworkflow_backend.background_processing.celery_tasks.process_instance_task_producer import (
    queue_future_task_if_appropriate,
)
from spiffworkflow_backend.background_processing.celery_tasks.process_instance_task_producer import (
    queue_process_instance_if_appropriate,
)
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.future_task import FutureTaskModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.task import TaskModel  # noqa: F401
from spiffworkflow_backend.services.process_instance_lock_service import ProcessInstanceLockService
from spiffworkflow_backend.services.process_instance_queue_service import ProcessInstanceIsAlreadyLockedError
from spiffworkflow_backend.services.process_instance_queue_service import ProcessInstanceQueueService
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService
from spiffworkflow_backend.services.process_instance_tmp_service import ProcessInstanceTmpService
from spiffworkflow_backend.services.workflow_execution_service import TaskRunnability
from celery.utils.log import get_task_logger
import redis


celery_task_logger = get_task_logger(__name__)

ten_minutes = 60 * 10


class SpiffCeleryWorkerError(Exception):
    pass


# Create a new Redis client
redis_client = redis.StrictRedis(host="localhost", port=6379, db=0)


# ignore types so we can use self and get the celery task id from self.request.id.
@shared_task(ignore_result=False, time_limit=ten_minutes, bind=True)
def celery_task_process_instance_run(self, process_instance_id: int, task_guid: str | None = None) -> dict:  # type: ignore
    proc_index = current_process().index

    message = f"celery_task_process_instance_run: process_instance_id: {process_instance_id} celery_task_id: {self.request.id}"
    if task_guid:
        message += f" task_guid: {task_guid}"
    celery_task_logger.info(message)

    ProcessInstanceLockService.set_thread_local_locking_context("celery:worker")
    process_instance = ProcessInstanceModel.query.filter_by(id=process_instance_id).first()

    if task_guid is None and ProcessInstanceTmpService.is_enqueued_to_run_in_the_future(process_instance):
        return {
            "ok": True,
            "process_instance_id": process_instance_id,
            "task_guid": task_guid,
            "message": "Skipped because the process instance is set to run in the future.",
        }
    try:
        task_guid_for_requeueing = task_guid
        with ProcessInstanceQueueService.dequeued(process_instance):
            # run ready tasks because...
            ProcessInstanceService.run_process_instance_with_processor(
                process_instance, execution_strategy_name="run_current_ready_tasks", should_schedule_waiting_timer_events=False
            )
            # we need to save instructions to the db so the frontend progress page can view them, and this is the only way to do it
            _processor, task_runnability = ProcessInstanceService.run_process_instance_with_processor(
                process_instance,
                execution_strategy_name="queue_instructions_for_end_user",
            )
            # currently, whenever we get a task_guid, that means that that task, which was a future task, is ready to run.
            # there is an assumption that it was successfully processed by run_process_instance_with_processor above.
            # we might want to check that assumption.
            if task_guid is not None:
                completed_task_model = (
                    TaskModel.query.filter_by(guid=task_guid)
                    .filter(TaskModel.state.in_(["COMPLETED", "ERROR", "CANCELLED"]))  # type: ignore
                    .first()
                )
                if completed_task_model is not None:
                    future_task = FutureTaskModel.query.filter_by(completed=False, guid=task_guid).first()
                    if future_task is not None:
                        future_task.completed = True
                        db.session.add(future_task)
                        db.session.commit()
                        task_guid_for_requeueing = None
        if task_runnability == TaskRunnability.has_ready_tasks:
            queue_process_instance_if_appropriate(process_instance, task_guid=task_guid_for_requeueing)
        return {"ok": True, "process_instance_id": process_instance_id, "task_guid": task_guid}
    except ProcessInstanceIsAlreadyLockedError as exception:
        celery_task_logger.info(
            f"Could not run process instance with worker: {current_app.config['PROCESS_UUID']} - {proc_index}. Error was:"
            f" {str(exception)}"
        )
        return {"ok": False, "process_instance_id": process_instance_id, "task_guid": task_guid, "exception": str(exception)}
    except Exception as exception:
        db.session.rollback()  # in case the above left the database with a bad transaction
        error_message = (
            f"Error running process_instance {process_instance.id} "
            + f"({process_instance.process_model_identifier}) and task_guid {task_guid}. {str(exception)}"
        )
        celery_task_logger.error(error_message)
        db.session.add(process_instance)
        db.session.commit()
        raise SpiffCeleryWorkerError(error_message) from exception
