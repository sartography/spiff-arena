import logging
from typing import Any

import celery

from spiffworkflow_backend import create_app
from spiffworkflow_backend.services.logging_service import configure_celery_stdout_logger
from spiffworkflow_backend.services.logging_service import get_log_formatter
from spiffworkflow_backend.services.logging_service import setup_logger_for_app

connexion_app = create_app()
the_flask_app = connexion_app.app

setting_variable_to_make_celery_happy_no_idea_how_this_works = the_flask_app.celery_app


@celery.signals.after_setup_logger.connect  # type: ignore
def setup_loggers(logger: Any, *args: Any, **kwargs: Any) -> None:
    log_formatter = get_log_formatter(the_flask_app)
    setup_logger_for_app(the_flask_app, logger, force_run_with_celery=True)
    log_level = logging.getLevelName(the_flask_app.config["SPIFFWORKFLOW_BACKEND_LOG_LEVEL"].upper())
    configure_celery_stdout_logger(logger, log_formatter, log_level)
    configure_celery_stdout_logger(the_flask_app.logger, log_formatter, log_level)
    for logger_name in ("celery.worker.strategy", "celery.app.trace"):
        configure_celery_stdout_logger(logging.getLogger(logger_name), log_formatter, log_level)


@celery.signals.after_setup_task_logger.connect  # type: ignore
def setup_task_logger(logger: Any, *args: Any, **kwargs: Any) -> None:
    configure_celery_stdout_logger(
        logger,
        get_log_formatter(the_flask_app),
        logging.getLevelName(the_flask_app.config["SPIFFWORKFLOW_BACKEND_LOG_LEVEL"].upper()),
    )


@celery.signals.task_prerun.connect  # type: ignore
def log_task_started(task_id: str, task: Any, *args: Any, **kwargs: Any) -> None:
    the_flask_app.logger.info(f"Celery task started: {task.name}[{task_id}]")


@celery.signals.task_postrun.connect  # type: ignore
def log_task_finished(task_id: str, task: Any, state: str, *args: Any, **kwargs: Any) -> None:
    the_flask_app.logger.info(f"Celery task finished: {task.name}[{task_id}] state={state}")
