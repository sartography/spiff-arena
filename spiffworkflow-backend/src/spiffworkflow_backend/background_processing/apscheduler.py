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


def start_apscheduler_if_appropriate(
    app: flask.app.Flask, scheduler_class: BaseScheduler = BackgroundScheduler
) -> None:
    if not should_start_apscheduler(app):
        return None

    scheduler = scheduler_class()

    # TODO: polling intervals for messages job
    polling_interval_in_seconds = app.config["SPIFFWORKFLOW_BACKEND_BACKGROUND_SCHEDULER_POLLING_INTERVAL_IN_SECONDS"]
    not_started_polling_interval_in_seconds = app.config[
        "SPIFFWORKFLOW_BACKEND_BACKGROUND_SCHEDULER_NOT_STARTED_POLLING_INTERVAL_IN_SECONDS"
    ]
    user_input_required_polling_interval_in_seconds = app.config[
        "SPIFFWORKFLOW_BACKEND_BACKGROUND_SCHEDULER_USER_INPUT_REQUIRED_POLLING_INTERVAL_IN_SECONDS"
    ]
    # TODO: add job to release locks to simplify other queries
    # TODO: add job to delete completed entires
    # TODO: add job to run old/low priority instances so they do not get drowned out

    scheduler.add_job(
        BackgroundProcessingService(app).process_message_instances_with_app_context,
        "interval",
        seconds=10,
    )
    scheduler.add_job(
        BackgroundProcessingService(app).process_not_started_process_instances,
        "interval",
        seconds=not_started_polling_interval_in_seconds,
    )
    scheduler.add_job(
        BackgroundProcessingService(app).process_waiting_process_instances,
        "interval",
        seconds=polling_interval_in_seconds,
    )
    scheduler.add_job(
        BackgroundProcessingService(app).process_user_input_required_process_instances,
        "interval",
        seconds=user_input_required_polling_interval_in_seconds,
    )
    scheduler.add_job(
        BackgroundProcessingService(app).remove_stale_locks,
        "interval",
        seconds=app.config["MAX_INSTANCE_LOCK_DURATION_IN_SECONDS"],
    )
    scheduler.start()
