from typing import Any

from billiard import current_process  # type: ignore
from celery import shared_task
from flask import current_app

from spiffworkflow_backend.background_processing.celery_tasks.process_instance_task_producer import (
    queue_process_instance_if_appropriate,
)
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.future_task import FutureTaskModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceCannotBeRunError
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.task import TaskModel  # noqa: F401
from spiffworkflow_backend.routes.process_api_blueprint import _get_process_model
from spiffworkflow_backend.services.process_instance_lock_service import ProcessInstanceLockService
from spiffworkflow_backend.services.process_instance_queue_service import ProcessInstanceIsAlreadyLockedError
from spiffworkflow_backend.services.process_instance_queue_service import ProcessInstanceQueueService
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService
from spiffworkflow_backend.services.process_instance_tmp_service import ProcessInstanceTmpService
from spiffworkflow_backend.services.workflow_execution_service import TaskRunnability

TEN_MINUTES = 60 * 10


class SpiffCeleryWorkerError(Exception):
    pass


@shared_task(ignore_result=False, time_limit=TEN_MINUTES, bind=True)
def celery_task_process_instance_update_notifier_run(
    self: Any,
    updated_process_instance_id: int,
    process_model_identifier: str,
    update_type: str,
) -> dict:
    celery_task_id = self.request.id
    logger_prefix = f"celery_task_process_instance_update_notifier_run[{celery_task_id}]"
    worker_intro_log_message = f"{logger_prefix}: updated_process_instance_id: {updated_process_instance_id}"
    current_app.logger.info(worker_intro_log_message)

    process_model = _get_process_model(current_app.config["SPIFFWORKFLOW_BACKEND_PROCESS_INSTANCE_UPDATE_PROCESS_MODEL"])
    data = {
        "update_type": update_type,
        "updated_process_instance_id": updated_process_instance_id,
        "process_model_identifier": process_model_identifier,
    }
    try:
        ProcessInstanceService.create_and_run_process_instance(
            process_model=process_model,
            persistence_level="none",
            data_to_inject=data,
        )
    except Exception as exception:
        error_message = (
            f"{logger_prefix}: Error notifying about updating process_instance {updated_process_instance_id}. {str(exception)}"
        )
        current_app.logger.error(error_message)
        raise SpiffCeleryWorkerError(error_message) from exception

    return {**{"ok": True}, **data}


# ignore types so we can use self and get the celery task id from self.request.id.
@shared_task(ignore_result=False, time_limit=TEN_MINUTES, bind=True)
def celery_task_process_instance_run(self, process_instance_id: int, task_guid: str | None = None) -> dict:  # type: ignore
    proc_index = current_process().index

    celery_task_id = self.request.id
    logger_prefix = f"celery_task_process_instance_run[{celery_task_id}]"
    worker_intro_log_message = f"{logger_prefix}: process_instance_id: {process_instance_id}"
    if task_guid:
        worker_intro_log_message += f" task_guid: {task_guid}"
    current_app.logger.info(worker_intro_log_message)

    ProcessInstanceLockService.set_thread_local_locking_context("celery:worker")
    process_instance = ProcessInstanceModel.query.filter_by(id=process_instance_id).first()

    skipped_mesage = None
    if process_instance is None:
        skipped_mesage = "Skipped because the process instance no longer exists in the database. It could have been deleted."
    elif task_guid is None and ProcessInstanceTmpService.is_enqueued_to_run_in_the_future(process_instance):
        skipped_mesage = "Skipped because the process instance is set to run in the future."
    if skipped_mesage is not None:
        return {
            "ok": True,
            "process_instance_id": process_instance_id,
            "task_guid": task_guid,
            "message": skipped_mesage,
        }

    try:
        task_guid_for_requeueing = task_guid
        with ProcessInstanceQueueService.dequeued(process_instance):
            # run ready tasks to force them to run in case they have instructions on them since queue_instructions_for_end_user
            # has a should_break_before that will exit if there are instructions.
            ProcessInstanceService.run_process_instance_with_processor(
                process_instance, execution_strategy_name="run_current_ready_tasks", should_schedule_waiting_timer_events=False
            )
            # we need to save instructions to the db so the frontend progress page can view them,
            # and this is the only way to do it
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
    except (ProcessInstanceIsAlreadyLockedError, ProcessInstanceCannotBeRunError) as exception:
        current_app.logger.info(
            f"{logger_prefix}: Could not run process instance with worker: {current_app.config['PROCESS_UUID']}"
            f" - {proc_index}. Error was: {str(exception)}"
        )
        return {"ok": False, "process_instance_id": process_instance_id, "task_guid": task_guid, "exception": str(exception)}
    except Exception as exception:
        db.session.rollback()  # in case the above left the database with a bad transaction
        error_message = (
            f"{logger_prefix}: Error running process_instance {process_instance_id} task_guid {task_guid}. {str(exception)}"
        )
        current_app.logger.error(error_message)
        db.session.add(process_instance)
        db.session.commit()
        raise SpiffCeleryWorkerError(error_message) from exception
