from spiffworkflow_backend.services.git_service import GitService


@shared_task(ignore_result=False, time_limit=ten_minutes, bind=True)
def celery_task_process_instance_run(self, process_instance_id: int, task_guid: str | None = None) -> dict:  # type: ignore
    try:
        GitService.commit(actions=["push"])
    except Exception as exception:
        error_message = f"{logger_prefix}: Error running git push from celery. {str(exception)}"
        current_app.logger.error(error_message)
        raise SpiffCeleryWorkerError(error_message) from exception
