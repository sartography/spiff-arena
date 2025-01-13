def queue_git_push_task() -> None:
    async_result = celery.current_app.send_task(
        "spiffworkflow_backend.background_processing.celery_tasks.git_service_task.celery_task_git_push"
    )
    message = f"Queueing a task to run git push. new celery task id: ({async_result.task_id})"
    current_app.logger.info(message)
