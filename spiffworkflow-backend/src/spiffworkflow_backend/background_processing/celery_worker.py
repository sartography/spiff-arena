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
    setup_logger_for_app(the_flask_app, force_run_with_celery=True)


@celery.signals.after_setup_task_logger.connect  # type: ignore
def setup_task_logger(logger: Any, *args: Any, **kwargs: Any) -> None:
    # Celery gives its task logger its own handler and level. Treat it like every other logger.
    logger.handlers = []
    logger.propagate = True
    logger.setLevel(logging.NOTSET)


@celery.signals.task_prerun.connect  # type: ignore
def log_task_started(task_id: str, task: Any, *args: Any, **kwargs: Any) -> None:
    the_flask_app.logger.info(f"Celery task started: {task.name}[{task_id}]")


@celery.signals.task_postrun.connect  # type: ignore
def log_task_finished(task_id: str, task: Any, state: str, *args: Any, **kwargs: Any) -> None:
    the_flask_app.logger.info(f"Celery task finished: {task.name}[{task_id}] state={state}")
