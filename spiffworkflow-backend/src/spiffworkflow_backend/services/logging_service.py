import json
import logging
import re
import sys
from typing import Any

from flask.app import Flask

# flask logging formats:
#   from: https://www.askpython.com/python-modules/flask/flask-logging
# %(asctime)s— The timestamp as a string.
# %(levelname)s—The logging level as a string.
# %(name)s—The logger name as a string.
# %(threadname)s—The thread name as a string.
# %(message)s—The log message.

# full message list:
# {'name': 'gunicorn.error', 'msg': 'GET /admin/token', 'args': (), 'levelname': 'DEBUG', 'levelno': 10, 'pathname': '~/.cache/pypoetry/virtualenvs/spiffworkflow-backend-R_hdWfN1-py3.10/lib/python3.10/site-packages/gunicorn/glogging.py', 'filename': 'glogging.py', 'module': 'glogging', 'exc_info': None, 'exc_text': None, 'stack_info': None, 'lineno': 267, 'funcName': 'debug', 'created': 1657307111.4513023, 'msecs': 451.30228996276855, 'relativeCreated': 1730.785846710205, 'thread': 139945864087360, 'threadName': 'MainThread', 'processName': 'MainProcess', 'process': 2109561, 'message': 'GET /admin/token', 'asctime': '2022-07-08T15:05:11.451Z'}  # noqa: E501


class InvalidLogLevelError(Exception):
    pass


# originally from https://stackoverflow.com/a/70223539/6090676


class JsonFormatter(logging.Formatter):
    """Formatter that outputs JSON strings after parsing the LogRecord.

    @param dict fmt_dict: Key: logging format attribute pairs. Defaults to {"message": "message"}.
    @param str time_format: time.strftime() format string. Default: "%Y-%m-%dT%H:%M:%S"
    @param str msec_format: Microsecond formatting. Appended at the end. Default: "%s.%03dZ"
    """

    def __init__(
        self,
        fmt_dict: dict | None = None,
        time_format: str = "%Y-%m-%dT%H:%M:%S",
        msec_format: str = "%s.%03dZ",
    ):
        self.fmt_dict = fmt_dict if fmt_dict is not None else {"message": "message"}
        self.default_time_format = time_format
        self.default_msec_format = msec_format
        self.datefmt = None

    def usesTime(self) -> bool:  # noqa: N802, this is overriding a method from python's stdlib
        """Overwritten to look for the attribute in the format dict values instead of the fmt string."""
        return "asctime" in self.fmt_dict.values()

    # we are overriding a method that returns a string and returning a dict, hence the Any
    def formatMessage(self, record: logging.LogRecord) -> Any:  # noqa: N802, this is overriding a method from python's stdlib
        """Overwritten to return a dictionary of the relevant LogRecord attributes instead of a string.

        KeyError is raised if an unknown attribute is provided in the fmt_dict.
        """
        return {fmt_key: record.__dict__[fmt_val] for fmt_key, fmt_val in self.fmt_dict.items()}

    def format(self, record: logging.LogRecord) -> str:
        """Mostly the same as the parent's class method.

        The difference being that a dict is manipulated and dumped as JSON instead of a string.
        """
        record.message = record.getMessage()

        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)

        message_dict = self.formatMessage(record)

        if record.exc_info:
            # Cache the traceback text to avoid converting it multiple times
            # (it's constant anyway)
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)

        if record.exc_text:
            message_dict["exc_info"] = record.exc_text

        if record.stack_info:
            message_dict["stack_info"] = self.formatStack(record.stack_info)

        return json.dumps(message_dict, default=str)


def setup_logger_for_app(app: Flask, primary_logger: Any) -> None:
    upper_log_level_string = app.config["SPIFFWORKFLOW_BACKEND_LOG_LEVEL"].upper()
    log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    if upper_log_level_string not in log_levels:
        raise InvalidLogLevelError(f"Log level given is invalid: '{upper_log_level_string}'. Valid options are {log_levels}")

    log_level = getattr(primary_logger, upper_log_level_string)
    spiff_log_level = getattr(primary_logger, upper_log_level_string)

    log_formatter = get_log_formatter(app)

    app.logger.debug("Printing log to create app logger")

    spiff_logger_filehandler = None
    if app.config["SPIFFWORKFLOW_BACKEND_LOG_TO_FILE"]:
        spiff_logger_filehandler = primary_logger.FileHandler(f"{app.instance_path}/../../log/{app.config['ENV_IDENTIFIER']}.log")
        spiff_logger_filehandler.setLevel(spiff_log_level)
        spiff_logger_filehandler.setFormatter(log_formatter)

    # these loggers have been deemed too verbose to be useful
    obscure_loggers_to_exclude_from_main_logging = ["connexion", "flask_cors.extension", "flask_cors.core", "sqlalchemy"]

    # if you actually want one of these excluded loggers, there is a config option to turn it on
    loggers_to_use = app.config.get("SPIFFWORKFLOW_BACKEND_LOGGERS_TO_USE", [])
    if loggers_to_use is None or loggers_to_use == "":
        loggers_to_use = []
    else:
        loggers_to_use = loggers_to_use.split(",")
    for logger_to_use in loggers_to_use:
        if logger_to_use in obscure_loggers_to_exclude_from_main_logging:
            obscure_loggers_to_exclude_from_main_logging.remove(logger_to_use)
        else:
            app.logger.warning(
                f"Logger '{logger_to_use}' not found in obscure_loggers_to_exclude_from_main_logging. "
                "You do not need to add it to SPIFFWORKFLOW_BACKEND_LOGGERS_TO_USE."
            )

    loggers_to_exclude_from_debug = []

    # even if we say SPIFFWORKFLOW_BACKEND_LOGGERS_TO_USE=sqlalchemy, we still don't want it in DEBUG mode, just INFO
    if "sqlalchemy" not in obscure_loggers_to_exclude_from_main_logging:
        loggers_to_exclude_from_debug.append("sqlalchemy")

    # NOTE: celery sets up handlers for all loggers by default. so if we want to stop some weird logger firehosing our logging,
    # we need to remove its handler or set its log level to a high level like ERROR. For example, sql alchemy seems to log all
    # queries at the INFO level and frickin query RESULTS as well if level is DEBUG.
    #
    # make all loggers act the same
    for name in primary_logger.root.manager.loggerDict:
        # use a regex so spiffworkflow_backend isn't filtered out
        if not re.match(r"^spiff\b", name):
            sub_logger = primary_logger.getLogger(name)
            sub_logger.setLevel(log_level)
            if spiff_logger_filehandler:
                sub_logger.handlers = []
                sub_logger.propagate = False
                sub_logger.addHandler(spiff_logger_filehandler)
            else:
                if len(sub_logger.handlers) < 1:
                    exclude_logger_name_from_logging = False
                    for logger_to_exclude in obscure_loggers_to_exclude_from_main_logging:
                        if name.startswith(logger_to_exclude):
                            exclude_logger_name_from_logging = True

                    # it's very verbose so set all obscure loggers to ERROR if not in DEBUG
                    if exclude_logger_name_from_logging or upper_log_level_string != "DEBUG":
                        sub_logger.setLevel("ERROR")

                    # only need to set the log level here if it is not already excluded from main logging
                    if not exclude_logger_name_from_logging and upper_log_level_string == "DEBUG":
                        exclude_logger_name_from_debug = False
                        for logger_to_exclude_from_debug in loggers_to_exclude_from_debug:
                            if name.startswith(logger_to_exclude_from_debug):
                                exclude_logger_name_from_debug = True
                        if exclude_logger_name_from_debug:
                            sub_logger.setLevel("INFO")

                    sub_logger.addHandler(primary_logger.StreamHandler(sys.stdout))

                for the_handler in sub_logger.handlers:
                    the_handler.setFormatter(log_formatter)
                    the_handler.setLevel(log_level)


def get_log_formatter(app: Flask) -> logging.Formatter:
    log_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # the json formatter is nice for real environments but makes
    # debugging locally a little more difficult
    if app.config["ENV_IDENTIFIER"] != "local_development":
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
    return log_formatter
