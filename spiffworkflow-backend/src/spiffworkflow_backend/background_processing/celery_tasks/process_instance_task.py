from datetime import datetime

from celery import shared_task
from flask import current_app
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.future_task import FutureTaskModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.services.process_instance_queue_service import ProcessInstanceQueueService
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService


def queue_enabled_for_process_model(process_instance: ProcessInstanceModel) -> bool:
    # TODO: check based on the process model itself as well
    return current_app.config["SPIFFWORKFLOW_BACKEND_CELERY_ENABLED"] is True


def queue_process_instance_if_appropriate(
    process_instance: ProcessInstanceModel, eta_in_seconds: float | None = None, task_guid: str | None = None
) -> bool:
    eta = None
    if eta_in_seconds is not None:
        eta = datetime.fromtimestamp(eta_in_seconds)
    if queue_enabled_for_process_model(process_instance) and process_instance.is_immediately_runnable():
        celery_task_process_instance_run.delay(process_instance.id, eta=eta, task_guid=task_guid)  # type: ignore
        return True

    return False


ten_minutes = 60 * 10


@shared_task(ignore_result=False, time_limit=ten_minutes)
def celery_task_process_instance_run(process_instance_id: int, task_guid: str | None = None) -> None:
    process_instance = ProcessInstanceModel.query.filter_by(id=process_instance_id).first()
    try:
        with ProcessInstanceQueueService.dequeued(process_instance):
            ProcessInstanceService.run_process_instance_with_processor(
                process_instance, execution_strategy_name="run_current_ready_tasks"
            )
            ProcessInstanceService.run_process_instance_with_processor(
                process_instance, execution_strategy_name="queue_instructions_for_end_user"
            )
            if task_guid is not None:
                future_task = FutureTaskModel.query.filter_by(completed=False, guid=task_guid).first()
                if future_task is not None:
                    future_task.completed = True
                    db.session.add(future_task)
                    db.session.commit()
            queue_process_instance_if_appropriate(process_instance)
    except Exception as e:
        db.session.rollback()  # in case the above left the database with a bad transaction
        error_message = (
            f"Error running process_instance {process_instance.id}" + f"({process_instance.process_model_identifier}). {str(e)}"
        )
        current_app.logger.error(error_message)
        db.session.add(process_instance)
        db.session.commit()
