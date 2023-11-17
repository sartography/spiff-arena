
from celery import shared_task  # type: ignore
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService


@shared_task(ignore_result=False)
def process_instance_task_run(process_instance_id: int) -> None:
    process_instance = ProcessInstanceModel.query.filter_by(id=process_instance_id).first()
    ProcessInstanceService.run_process_instance_with_processor(process_instance, execution_strategy_name="greedy")
    if process_instance.is_immediately_runnable():
        process_instance_task_run.delay(process_instance.id)
