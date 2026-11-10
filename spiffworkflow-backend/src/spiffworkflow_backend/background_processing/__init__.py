# The soft limit raises SoftTimeLimitExceeded in the job, which records the error and releases the lock like any other
# failure. The hard limit kills the worker if the job is still going after that. Config setup makes sure the hard limit
# is below MAX_INSTANCE_LOCK_DURATION_IN_SECONDS, so a job is over before its lock can be removed as stale and its
# process instance run again.
CELERY_TASK_SOFT_TIME_LIMIT_IN_SECONDS = 240
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
