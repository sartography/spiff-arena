import os

import flask.wrappers
from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore
from apscheduler.schedulers.base import BaseScheduler  # type: ignore

from spiffworkflow_backend.background_processing.background_processing_service import BackgroundProcessingService


def should_start_apscheduler(app: flask.app.Flask) -> bool:
    if not app.config["SPIFFWORKFLOW_BACKEND_RUN_BACKGROUND_SCHEDULER_IN_CREATE_APP"]:
        return False

    # do not start the scheduler twice in flask debug mode but support code reloading
    if app.config["ENV_IDENTIFIER"] == "local_development" and os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        return False

    return True


def start_apscheduler_if_appropriate(app: flask.app.Flask, scheduler_class: BaseScheduler = BackgroundScheduler) -> None:
    if not should_start_apscheduler(app):
        return None

    start_apscheduler(app, scheduler_class)


def start_apscheduler(app: flask.app.Flask, scheduler_class: BaseScheduler = BackgroundScheduler) -> None:
    scheduler = scheduler_class()

    if app.config["SPIFFWORKFLOW_BACKEND_CELERY_ENABLED"]:
        _add_jobs_for_celery_based_configuration(app, scheduler)
    else:
        _add_jobs_for_non_celery_based_configuration(app, scheduler)

    _add_jobs_that_should_run_regardless_of_celery_config(app, scheduler)

    scheduler.start()


def _add_jobs_for_celery_based_configuration(app: flask.app.Flask, scheduler: BaseScheduler) -> None:
    future_task_execution_interval_in_seconds = app.config[
        "SPIFFWORKFLOW_BACKEND_BACKGROUND_SCHEDULER_FUTURE_TASK_EXECUTION_INTERVAL_IN_SECONDS"
    ]

    scheduler.add_job(
        BackgroundProcessingService(app).process_future_tasks,
        "interval",
        seconds=future_task_execution_interval_in_seconds,
    )


def _add_jobs_for_non_celery_based_configuration(app: flask.app.Flask, scheduler: BaseScheduler) -> None:
    # TODO: polling intervals for messages job
    polling_interval_in_seconds = app.config["SPIFFWORKFLOW_BACKEND_BACKGROUND_SCHEDULER_POLLING_INTERVAL_IN_SECONDS"]
    user_input_required_polling_interval_in_seconds = app.config[
        "SPIFFWORKFLOW_BACKEND_BACKGROUND_SCHEDULER_USER_INPUT_REQUIRED_POLLING_INTERVAL_IN_SECONDS"
    ]
    # TODO: add job to release locks to simplify other queries
    # TODO: add job to delete completed entires
    # TODO: add job to run old/low priority instances so they do not get drowned out

    # we should be able to remove these once we switch over to future tasks for non-celery configuration
    scheduler.add_job(
        BackgroundProcessingService(app).process_waiting_process_instances,
        "interval",
        seconds=polling_interval_in_seconds,
    )
    scheduler.add_job(
        BackgroundProcessingService(app).process_running_process_instances,
        "interval",
        seconds=polling_interval_in_seconds,
    )
    scheduler.add_job(
        BackgroundProcessingService(app).process_user_input_required_process_instances,
        "interval",
        seconds=user_input_required_polling_interval_in_seconds,
    )


def _add_jobs_that_should_run_regardless_of_celery_config(app: flask.app.Flask, scheduler: BaseScheduler) -> None:
    not_started_polling_interval_in_seconds = app.config[
        "SPIFFWORKFLOW_BACKEND_BACKGROUND_SCHEDULER_NOT_STARTED_POLLING_INTERVAL_IN_SECONDS"
    ]

    # TODO: see if we can queue with celery instead on celery based configuration
    scheduler.add_job(
        BackgroundProcessingService(app).process_message_instances_with_app_context,
        "interval",
        seconds=10,
    )

    # when you create a process instance via the API and do not use the run API method, this would pick up the instance.
    scheduler.add_job(
        BackgroundProcessingService(app).process_not_started_process_instances,
        "interval",
        seconds=not_started_polling_interval_in_seconds,
    )
    scheduler.add_job(
        BackgroundProcessingService(app).remove_stale_locks,
        "interval",
        seconds=app.config["MAX_INSTANCE_LOCK_DURATION_IN_SECONDS"],
    )
