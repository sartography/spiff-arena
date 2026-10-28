import logging
from typing import Any

import celery

from spiffworkflow_backend import create_app
from spiffworkflow_backend.services.logging_service import setup_logger_for_app

connexion_app = create_app()
the_flask_app = connexion_app.app

setting_variable_to_make_celery_happy_no_idea_how_this_works = the_flask_app.celery_app


@celery.signals.after_setup_logger.connect  # type: ignore
def setup_loggers(*args: Any, **kwargs: Any) -> None:
    # Celery replaces the root handler with its own, so set up our logging again.
    setup_logger_for_app(the_flask_app, celery_worker=True)


@celery.signals.after_setup_task_logger.connect  # type: ignore
def setup_task_logger(logger: Any, *args: Any, **kwargs: Any) -> None:
    # Celery gives its task logger its own handler and level. Treat it like every other logger.
    logger.handlers = []
    logger.propagate = True
    logger.setLevel(logging.NOTSET)
