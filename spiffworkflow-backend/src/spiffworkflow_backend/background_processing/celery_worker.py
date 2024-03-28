import logging

import celery
from flask.helpers import sys

from spiffworkflow_backend import create_app
from spiffworkflow_backend.background_processing.celery_tasks.process_instance_task import (
    celery_task_process_instance_run,  # noqa: F401
)
from spiffworkflow_backend.services.logging_service import setup_logger

the_flask_app = create_app()
# logger = get_task_logger("awesome_celery_logger")


# @celery.signals.setup_logging.connect
# def on_setup_logging(**kwargs):
#     pass
#     # # print(f"kwargs", kwargs)
#     # # pass
#     # return kwargs
#     # from logging.config import dictConfig
#     #
#     # dictConfig(the_flask_app.logger)
#     setup_logger(the_flask_app)


@celery.signals.after_setup_logger.connect
def setup_loggers(logger, *args, **kwargs):
    logger.handlers = []
    stdout_handler = logging.StreamHandler(sys.stdout)
    logger.addHandler(stdout_handler)
    print("IN CELERY")
    setup_logger(the_flask_app, logger)
    # logging.basicConfig()
    # logging.getLogger("sqlalchemy").setLevel(logging.ERROR)
    # logging.disable(logging.WARNING)

    # # logger.addHandler(logging.StreamHandler(sys.stdout))
    # print(f"logger", logger.manager.loggerDict)
    # logger.setLevel("INFO")
    # stdout_handler = logging.StreamHandler(sys.stdout)
    # stdout_handler.setLevel("INFO")
    # log_formatter = JsonFormatter(
    #     {
    #         "level": "levelname",
    #         "message": "message",
    #         "loggerName": "name",
    #         "processName": "processName",
    #         "processID": "process",
    #         "threadName": "threadName",
    #         "threadID": "thread",
    #         "timestamp": "asctime",
    #     }
    # )
    # stdout_handler.formatter = log_formatter
    # logger.handlers = []
    # logger.addHandler(stdout_handler)
    #
    # for name in logging.root.manager.loggerDict:
    #     # use a regex so spiffworkflow_backend isn't filtered out
    #     if not re.match(r"^spiff\b", name):
    #         the_logger = logging.getLogger(name)
    #         the_logger.setLevel("INFO")
    #         # it's very verbose, so only add handlers for the obscure loggers when log level is DEBUG
    #         # if upper_log_level_string == "DEBUG":
    #         #     if len(the_logger.handlers) < 1:
    #         #         exclude_logger_name_from_logging = False
    #         #         for garbage_logger in garbage_loggers_to_exclude:
    #         #             if name.startswith(garbage_logger):
    #         #                 exclude_logger_name_from_logging = True
    #         #
    #         #         exclude_logger_name_from_debug = False
    #         #         for logger_to_exclude_from_debug in loggers_to_exclude_from_debug:
    #         #             if name.startswith(logger_to_exclude_from_debug):
    #         #                 exclude_logger_name_from_debug = True
    #         #         if exclude_logger_name_from_debug:
    #         #             the_logger.setLevel("ERROR")
    #         #
    #         #         if not exclude_logger_name_from_logging:
    #         #             the_logger.addHandler(logging.StreamHandler(sys.stdout))
    #         #
    #         for the_handler in the_logger.handlers:
    #             the_handler.setFormatter(log_formatter)
    #             the_handler.setLevel("INFO")
    # # formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    # #
    # # # FileHandler
    # # fh = logging.FileHandler("logs.log")
    # # fh.setFormatter(formatter)
    # # logger.addHandler(fh)
    # #
    # # # SysLogHandler
    # # slh = logging.handlers.SysLogHandler(address=("logsN.papertrailapp.com", "..."))
    # # slh.setFormatter(formatter)
    # # logger.addHandler(slh)


setting_variable_to_make_celery_happy_no_idea_how_this_works = the_flask_app.celery_app
