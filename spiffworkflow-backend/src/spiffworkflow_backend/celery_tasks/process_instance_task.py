from celery import shared_task
from spiffworkflow_backend.services.process_instance_lock_service import ProcessInstanceLockService
from spiffworkflow_backend.models.db import db
from flask import current_app

from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService


def queue_process_instance_if_appropriate(process_instance: ProcessInstanceModel) -> bool:
    if current_app.config['SPIFFWORKFLOW_BACKEND_CELERY_ENABLED'] and process_instance.is_immediately_runnable():
        process_instance_task_run.delay(process_instance.id)
        return True

    return False


ten_minutes = 60 * 10

@shared_task(ignore_result=False, time_limit=ten_minutes)  # type: ignore
def process_instance_task_run(process_instance_id: int) -> None:
    process_instance = ProcessInstanceModel.query.filter_by(id=process_instance_id).first()
    try:
        ProcessInstanceService.run_process_instance_with_processor(
            process_instance, execution_strategy_name="run_current_ready_tasks"
        )
        ProcessInstanceService.run_process_instance_with_processor(
            process_instance, execution_strategy_name="queue_instructions_for_end_user"
        )
        queue_process_instance_if_appropriate(process_instance)
    except Exception as e:
        db.session.rollback()  # in case the above left the database with a bad transaction
        error_message = (
            f"Error running process_instance {process_instance.id}"
            + f"({process_instance.process_model_identifier}). {str(e)}"
        )
        current_app.logger.error(error_message)
        db.session.add(process_instance)
        db.session.commit()
