import logging
import sys
from typing import Any

import celery

from spiffworkflow_backend import create_app

from spiffworkflow_backend.services.logging_service import get_log_formatter
from spiffworkflow_backend.services.logging_service import setup_logger_for_app

connexion_app = create_app()
the_flask_app = connexion_app.app

setting_variable_to_make_celery_happy_no_idea_how_this_works = the_flask_app.celery_app


@celery.signals.after_setup_logger.connect  # type: ignore
def setup_loggers(logger: Any, *args: Any, **kwargs: Any) -> None:
    log_formatter = get_log_formatter(the_flask_app)
    logger.handlers = []
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(log_formatter)
    logger.addHandler(stdout_handler)
    setup_logger_for_app(the_flask_app, logger, force_run_with_celery=True)
