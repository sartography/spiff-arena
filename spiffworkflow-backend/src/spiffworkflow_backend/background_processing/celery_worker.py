import celery

from spiffworkflow_backend import create_app
from spiffworkflow_backend.background_processing.celery_tasks.process_instance_task import (
    celery_task_process_instance_run,  # noqa: F401
)

the_flask_app = create_app()
# logger = get_task_logger("awesome_celery_logger")


# @celery.signals.setup_logging.connect
# def on_setup_logging(**kwargs):
#     # # print(f"kwargs", kwargs)
#     # # pass
#     # return kwargs
#     from logging.config import dictConfig
#
#     dictConfig(the_flask_app.logger)


@celery.signals.after_setup_logger.connect
def setup_loggers(logger, *args, **kwargs):
    logger.level = 50
    print("logger.level", logger.level)
    # formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    #
    # # FileHandler
    # fh = logging.FileHandler("logs.log")
    # fh.setFormatter(formatter)
    # logger.addHandler(fh)
    #
    # # SysLogHandler
    # slh = logging.handlers.SysLogHandler(address=("logsN.papertrailapp.com", "..."))
    # slh.setFormatter(formatter)
    # logger.addHandler(slh)


setting_variable_to_make_celery_happy_no_idea_how_this_works = the_flask_app.celery_app
