import logging
import sys
from typing import Any

import celery

from spiffworkflow_backend import create_app

# we need to import tasks from this file so they can be used elsewhere in the app
from spiffworkflow_backend.background_processing.celery_tasks.process_instance_task import (
    celery_task_process_instance_run,  # noqa: F401
)
from spiffworkflow_backend.services.logging_service import JsonFormatter
from spiffworkflow_backend.services.logging_service import setup_logger_for_app

the_flask_app = create_app()

setting_variable_to_make_celery_happy_no_idea_how_this_works = the_flask_app.celery_app


@celery.signals.after_setup_logger.connect  # type: ignore
def setup_loggers(logger: Any, *args: Any, **kwargs: Any) -> None:
    # upper_log_level_string = the_flask_app.config["SPIFFWORKFLOW_BACKEND_LOG_LEVEL"].upper()
    # log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    #
    # if upper_log_level_string not in log_levels:
    #     raise InvalidLogLevelError(f"Log level given is invalid: '{upper_log_level_string}'. Valid options are {log_levels}")
    #
    # log_level = getattr(logging, upper_log_level_string)
    log_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    #
    # logger.debug("Printing log to create app logger")
    #
    if the_flask_app.config["ENV_IDENTIFIER"] != "local_development":
        json_formatter = JsonFormatter(
            {
                "level": "levelname",
                "message": "message",
                "loggerName": "name",
                "processName": "processName",
                "processID": "process",
                "threadName": "threadName",
                "threadID": "thread",
                "timestamp": "asctime",
            }
        )
        log_formatter = json_formatter

    logger.handlers = []
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(log_formatter)
    logger.addHandler(stdout_handler)
    setup_logger_for_app(the_flask_app, logger)
