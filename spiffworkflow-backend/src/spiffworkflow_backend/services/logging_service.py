"""Logging_service."""
import json
import logging
import re
from typing import Any
from typing import Optional

from flask import g
from flask.app import Flask

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.spiff_logging import SpiffLoggingModel


# flask logging formats:
#   from: https://www.askpython.com/python-modules/flask/flask-logging
# %(asctime)s— The timestamp as a string.
# %(levelname)s—The logging level as a string.
# %(name)s—The logger name as a string.
# %(threadname)s—The thread name as a string.
# %(message)s—The log message.

# full message list:
# {'name': 'gunicorn.error', 'msg': 'GET /admin/token', 'args': (), 'levelname': 'DEBUG', 'levelno': 10, 'pathname': '~/.cache/pypoetry/virtualenvs/spiffworkflow-backend-R_hdWfN1-py3.10/lib/python3.10/site-packages/gunicorn/glogging.py', 'filename': 'glogging.py', 'module': 'glogging', 'exc_info': None, 'exc_text': None, 'stack_info': None, 'lineno': 267, 'funcName': 'debug', 'created': 1657307111.4513023, 'msecs': 451.30228996276855, 'relativeCreated': 1730.785846710205, 'thread': 139945864087360, 'threadName': 'MainThread', 'processName': 'MainProcess', 'process': 2109561, 'message': 'GET /admin/token', 'asctime': '2022-07-08T15:05:11.451Z'}


class InvalidLogLevelError(Exception):
    """InvalidLogLevelError."""


# originally from https://stackoverflow.com/a/70223539/6090676


class JsonFormatter(logging.Formatter):
    """Formatter that outputs JSON strings after parsing the LogRecord.

    @param dict fmt_dict: Key: logging format attribute pairs. Defaults to {"message": "message"}.
    @param str time_format: time.strftime() format string. Default: "%Y-%m-%dT%H:%M:%S"
    @param str msec_format: Microsecond formatting. Appended at the end. Default: "%s.%03dZ"
    """

    def __init__(
        self,
        fmt_dict: Optional[dict] = None,
        time_format: str = "%Y-%m-%dT%H:%M:%S",
        msec_format: str = "%s.%03dZ",
    ):
        """__init__."""
        self.fmt_dict = fmt_dict if fmt_dict is not None else {"message": "message"}
        self.default_time_format = time_format
        self.default_msec_format = msec_format
        self.datefmt = None

    def usesTime(self) -> bool:
        """Overwritten to look for the attribute in the format dict values instead of the fmt string."""
        return "asctime" in self.fmt_dict.values()

    # we are overriding a method that returns a string and returning a dict, hence the Any
    def formatMessage(self, record: logging.LogRecord) -> Any:
        """Overwritten to return a dictionary of the relevant LogRecord attributes instead of a string.

        KeyError is raised if an unknown attribute is provided in the fmt_dict.
        """
        return {
            fmt_key: record.__dict__[fmt_val]
            for fmt_key, fmt_val in self.fmt_dict.items()
        }

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


class SpiffFilter(logging.Filter):
    """SpiffFilter."""

    def __init__(self, app: Flask):
        """__init__."""
        self.app = app
        super().__init__()

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter."""
        tld = self.app.config["THREAD_LOCAL_DATA"]
        process_instance_id = ""
        if hasattr(tld, "process_instance_id"):
            process_instance_id = tld.process_instance_id
        setattr(record, "process_instance_id", process_instance_id)  # noqa: B010
        if hasattr(tld, "spiff_step"):
            setattr(record, "spiff_step", tld.spiff_step)  # noqa: 8010
        if hasattr(g, "user") and g.user:
            setattr(record, "current_user_id", g.user.id)  # noqa: B010
        return True


def setup_logger(app: Flask) -> None:
    """Setup_logger."""
    upper_log_level_string = app.config["SPIFFWORKFLOW_BACKEND_LOG_LEVEL"].upper()
    log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    if upper_log_level_string not in log_levels:
        raise InvalidLogLevelError(
            f"Log level given is invalid: '{upper_log_level_string}'. Valid options are"
            f" {log_levels}"
        )

    log_level = getattr(logging, upper_log_level_string)
    spiff_log_level = getattr(logging, upper_log_level_string)
    log_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    app.logger.debug("Printing log to create app logger")

    # the json formatter is nice for real environments but makes
    # debugging locally a little more difficult
    if app.config["ENV_IDENTIFIER"] != "development":
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

    spiff_logger_filehandler = None
    if app.config["SPIFFWORKFLOW_BACKEND_LOG_TO_FILE"]:
        spiff_logger_filehandler = logging.FileHandler(
            f"{app.instance_path}/../../log/{app.config['ENV_IDENTIFIER']}.log"
        )
        spiff_logger_filehandler.setLevel(spiff_log_level)
        spiff_logger_filehandler.setFormatter(log_formatter)

    # make all loggers act the same
    for name in logging.root.manager.loggerDict:
        # use a regex so spiffworkflow_backend isn't filtered out
        if not re.match(r"^spiff\b", name):
            the_logger = logging.getLogger(name)
            the_logger.setLevel(log_level)
            if spiff_logger_filehandler:
                the_logger.handlers = []
                the_logger.propagate = False
                the_logger.addHandler(spiff_logger_filehandler)
            else:
                for the_handler in the_logger.handlers:
                    the_handler.setFormatter(log_formatter)
                    the_handler.setLevel(log_level)

    spiff_logger = logging.getLogger("spiff")
    spiff_logger.setLevel(spiff_log_level)
    spiff_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s | %(action)s | %(task_type)s |"
        " %(process)s | %(processName)s | %(process_instance_id)s"
    )

    # if you add a handler to spiff, it will be used/inherited by spiff.metrics
    # if you add a filter to the spiff logger directly (and not the handler), it will NOT be inherited by spiff.metrics
    # so put filters on handlers.
    db_handler = DBHandler()
    db_handler.setLevel(spiff_log_level)
    db_handler.setFormatter(spiff_formatter)
    db_handler.addFilter(SpiffFilter(app))
    spiff_logger.addHandler(db_handler)


# https://9to5answer.com/python-logging-to-database
class DBHandler(logging.Handler):
    """DBHandler."""

    def __init__(self) -> None:
        """__init__."""
        self.logs: list[dict] = []
        super().__init__()

    def bulk_insert_logs(self) -> None:
        """Bulk_insert_logs."""
        db.session.bulk_insert_mappings(SpiffLoggingModel, self.logs)
        db.session.commit()
        self.logs = []

    def emit(self, record: logging.LogRecord) -> None:
        """Emit."""
        # if we do not have a process instance id then do not log and assume we are running a script unit test
        # that initializes a BpmnWorkflow without a process instance
        if record and record.process_instance_id:  # type: ignore
            bpmn_process_identifier = record.workflow  # type: ignore
            spiff_task_guid = str(record.task_id)  # type: ignore
            bpmn_task_identifier = str(record.task_spec)  # type: ignore
            bpmn_task_name = record.task_name if hasattr(record, "task_name") else None  # type: ignore
            bpmn_task_type = record.task_type if hasattr(record, "task_type") else None  # type: ignore
            timestamp = record.created
            message = record.msg if hasattr(record, "msg") else None
            current_user_id = (
                record.current_user_id if hasattr(record, "current_user_id") else None  # type: ignore
            )
            spiff_step = (
                record.spiff_step  # type: ignore
                if hasattr(record, "spiff_step") and record.spiff_step is not None  # type: ignore
                else 1
            )
            self.logs.append(
                {
                    "process_instance_id": record.process_instance_id,  # type: ignore
                    "bpmn_process_identifier": bpmn_process_identifier,
                    "spiff_task_guid": spiff_task_guid,
                    "bpmn_task_name": bpmn_task_name,
                    "bpmn_task_identifier": bpmn_task_identifier,
                    "bpmn_task_type": bpmn_task_type,
                    "message": message,
                    "timestamp": timestamp,
                    "current_user_id": current_user_id,
                    "spiff_step": spiff_step,
                }
            )
            # so at some point we are going to insert logs.
            # we don't want to insert on every log, so we will insert every 100 logs, which is just about as fast as inserting
            # on every 1,000 logs. if we get deadlocks in the database, this can be changed to 1 in order to insert on every log.
            if len(self.logs) >= 100:
                self.bulk_insert_logs()
