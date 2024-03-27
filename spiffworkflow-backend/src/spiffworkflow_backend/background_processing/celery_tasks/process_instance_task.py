from billiard import current_process  # type: ignore
from celery import shared_task
from flask import current_app

from spiffworkflow_backend.background_processing.celery_tasks.process_instance_task_producer import (
    queue_process_instance_if_appropriate,
)
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.future_task import FutureTaskModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.services.process_instance_lock_service import ProcessInstanceLockService
from spiffworkflow_backend.services.process_instance_queue_service import ProcessInstanceIsAlreadyLockedError
from spiffworkflow_backend.services.process_instance_queue_service import ProcessInstanceQueueService
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService
from spiffworkflow_backend.services.workflow_execution_service import TaskRunnability

ten_minutes = 60 * 10


@shared_task(ignore_result=False, time_limit=ten_minutes)
def celery_task_process_instance_run(process_instance_id: int, task_guid: str | None = None) -> dict:
    proc_index = current_process().index
    ProcessInstanceLockService.set_thread_local_locking_context("celery:worker", additional_processing_identifier=proc_index)
    process_instance = ProcessInstanceModel.query.filter_by(id=process_instance_id).first()
    try:
        with ProcessInstanceQueueService.dequeued(process_instance, additional_processing_identifier=proc_index):
            ProcessInstanceService.run_process_instance_with_processor(
                process_instance, execution_strategy_name="run_current_ready_tasks", additional_processing_identifier=proc_index
            )
            _processor, task_runnability = ProcessInstanceService.run_process_instance_with_processor(
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
        return {"ok": True, "process_instance_id": process_instance_id, "task_guid": task_guid}
    except ProcessInstanceIsAlreadyLockedError as exception:
        current_app.logger.info(
            f"Could not run process instance with worker: {current_app.config['PROCESS_UUID']} - {proc_index}. Error was:"
            f" {str(exception)}"
        )
        return {"ok": False, "process_instance_id": process_instance_id, "task_guid": task_guid, "exception": str(exception)}
    except Exception as e:
        db.session.rollback()  # in case the above left the database with a bad transaction
        error_message = (
            f"Error running process_instance {process_instance.id}" + f"({process_instance.process_model_identifier}). {str(e)}"
        )
        current_app.logger.error(error_message)
        db.session.add(process_instance)
        db.session.commit()
        raise e
