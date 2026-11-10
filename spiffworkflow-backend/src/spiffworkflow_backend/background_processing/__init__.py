# A job still running at this point has its worker killed. Config setup makes sure this is below
# MAX_INSTANCE_LOCK_DURATION_IN_SECONDS, so a job is over before its lock can be removed as stale and its process
# instance run again.
CELERY_TASK_TIME_LIMIT_IN_SECONDS = 270

CELERY_TASK_PROCESS_INSTANCE_RUN = (
    "spiffworkflow_backend.background_processing.celery_tasks.process_instance_task.celery_task_process_instance_run"
)
CELERY_TASK_PROCESS_INSTANCE_START_FROM_MODEL = (
    "spiffworkflow_backend.background_processing.celery_tasks.process_instance_task.celery_task_process_instance_start_from_model"  # noqa: E501
)
CELERY_TASK_PROCESS_INSTANCE_START_FROM_MESSAGE = "spiffworkflow_backend.background_processing.celery_tasks.process_instance_task.celery_task_process_instance_start_from_message"  # noqa: E501
CELERY_TASK_EVENT_NOTIFIER = (
    "spiffworkflow_backend.background_processing.celery_tasks.process_instance_task.celery_task_event_notifier_run"  # noqa: E501
)
