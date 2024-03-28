import logging
import re
import sys
from typing import Any

import celery

from spiffworkflow_backend import create_app

# we need to import tasks from this file so they can be used elsewhere in the app
from spiffworkflow_backend.background_processing.celery_tasks.process_instance_task import (
    celery_task_process_instance_run,  # noqa: F401
)
from spiffworkflow_backend.services.logging_service import InvalidLogLevelError
from spiffworkflow_backend.services.logging_service import JsonFormatter

the_flask_app = create_app()


@celery.signals.after_setup_logger.connect  # type: ignore
def setup_loggers(logger: Any, *args: Any, **kwargs: Any) -> None:
    upper_log_level_string = the_flask_app.config["SPIFFWORKFLOW_BACKEND_LOG_LEVEL"].upper()
    log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    if upper_log_level_string not in log_levels:
        raise InvalidLogLevelError(f"Log level given is invalid: '{upper_log_level_string}'. Valid options are {log_levels}")

    log_level = getattr(logging, upper_log_level_string)
    log_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    logger.debug("Printing log to create app logger")

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

    # these loggers have been deemed too verbose to be useful
    garbage_loggers_to_exclude = ["connexion", "flask_cors.extension", "flask_cors.core", "sqlalchemy"]

    # if you actually want one of these excluded loggers, there is a config option to turn it on
    loggers_to_use = the_flask_app.config.get("SPIFFWORKFLOW_BACKEND_LOGGERS_TO_USE", [])
    if loggers_to_use is None or loggers_to_use == "":
        loggers_to_use = []
    else:
        loggers_to_use = loggers_to_use.split(",")
    for logger_to_use in loggers_to_use:
        if logger_to_use in garbage_loggers_to_exclude:
            garbage_loggers_to_exclude.remove(logger_to_use)
        else:
            the_flask_app.logger.warning(
                f"Logger '{logger_to_use}' not found in garbage_loggers_to_exclude. You do not need to add it to"
                " SPIFFWORKFLOW_BACKEND_LOGGERS_TO_USE."
            )

    loggers_to_exclude_from_debug = []

    if "sqlalchemy" not in garbage_loggers_to_exclude:
        loggers_to_exclude_from_debug.append("sqlalchemy")

    # make all loggers act the same
    for name in logging.root.manager.loggerDict:
        # use a regex so spiffworkflow_backend isn't filtered out
        if not re.match(r"^spiff\b", name):
            the_logger = logging.getLogger(name)
            the_logger.setLevel(log_level)
            # it's very verbose, so only add handlers for the obscure loggers when log level is DEBUG
            if upper_log_level_string == "DEBUG":
                if len(the_logger.handlers) < 1:
                    exclude_logger_name_from_logging = False
                    for garbage_logger in garbage_loggers_to_exclude:
                        if name.startswith(garbage_logger):
                            exclude_logger_name_from_logging = True

                    exclude_logger_name_from_debug = False
                    for logger_to_exclude_from_debug in loggers_to_exclude_from_debug:
                        if name.startswith(logger_to_exclude_from_debug):
                            exclude_logger_name_from_debug = True
                    if exclude_logger_name_from_debug:
                        the_logger.setLevel("INFO")

                    if exclude_logger_name_from_logging:
                        the_logger.setLevel("ERROR")
                    the_logger.addHandler(logging.StreamHandler(sys.stdout))

            for the_handler in the_logger.handlers:
                the_handler.setFormatter(log_formatter)
                the_handler.setLevel(log_level)


setting_variable_to_make_celery_happy_no_idea_how_this_works = the_flask_app.celery_app
