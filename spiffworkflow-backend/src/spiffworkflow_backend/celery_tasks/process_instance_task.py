from celery import shared_task
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
    ProcessInstanceService.run_process_instance_with_processor(
        process_instance, execution_strategy_name="run_current_ready_tasks"
    )
    ProcessInstanceService.run_process_instance_with_processor(
        process_instance, execution_strategy_name="queue_instructions_for_end_user"
    )
    queue_process_instance_if_appropriate(process_instance)
