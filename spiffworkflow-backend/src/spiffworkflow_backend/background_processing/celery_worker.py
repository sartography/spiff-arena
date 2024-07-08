import logging
import sys
from typing import Any

import celery

from spiffworkflow_backend import create_app

# we need to import tasks from this file so they can be used elsewhere in the app
from spiffworkflow_backend.background_processing.celery_tasks.process_instance_task import (
    celery_task_process_instance_run,  # noqa: F401
)
from spiffworkflow_backend.services.logging_service import get_log_formatter
from spiffworkflow_backend.services.logging_service import setup_logger_for_app

the_flask_app = create_app()

setting_variable_to_make_celery_happy_no_idea_how_this_works = the_flask_app.celery_app


@celery.signals.after_setup_logger.connect  # type: ignore
def setup_loggers(logger: Any, *args: Any, **kwargs: Any) -> None:
    log_formatter = get_log_formatter(the_flask_app)
    logger.handlers = []
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(log_formatter)
    logger.addHandler(stdout_handler)
    setup_logger_for_app(the_flask_app, logger, force_run_with_celery=True)
    # this handler is getting added somewhere but not sure where so set its
    # level really high since we do not need it
    logging.getLogger("spiff").setLevel(logging.CRITICAL)
