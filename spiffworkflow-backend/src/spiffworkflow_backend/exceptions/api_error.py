"""API Error functionality."""
from __future__ import annotations

import json
from dataclasses import dataclass
from dataclasses import field
from typing import Any

import flask.wrappers
import sentry_sdk
from flask import Blueprint
from flask import current_app
from flask import g
from flask import jsonify
from flask import make_response
from sentry_sdk import capture_exception
from sentry_sdk import set_tag
from SpiffWorkflow.exceptions import SpiffWorkflowException  # type: ignore
from SpiffWorkflow.exceptions import WorkflowException
from SpiffWorkflow.exceptions import WorkflowTaskException
from SpiffWorkflow.specs.base import TaskSpec  # type: ignore
from SpiffWorkflow.task import Task  # type: ignore

from spiffworkflow_backend.services.authentication_service import NotAuthorizedError
from spiffworkflow_backend.services.authentication_service import TokenInvalidError
from spiffworkflow_backend.services.authentication_service import TokenNotProvidedError
from spiffworkflow_backend.services.authentication_service import UserNotLoggedInError


api_error_blueprint = Blueprint("api_error_blueprint", __name__)


@dataclass
class ApiError(Exception):
    """ApiError Class to help handle exceptions."""

    error_code: str
    message: str
    error_line: str = ""
    error_type: str = ""
    file_name: str = ""
    line_number: int = 0
    offset: int = 0
    sentry_link: str | None = None
    status_code: int = 400
    tag: str = ""
    task_data: dict | str | None = field(default_factory=dict)
    task_id: str = ""
    task_name: str = ""
    task_trace: list | None = field(default_factory=list)

    def __str__(self) -> str:
        """Instructions to print instance as a string."""
        msg = "ApiError: % s. " % self.message
        if self.task_name:
            msg += f"Error in task '{self.task_name}' ({self.task_id}). "
        if self.line_number:
            msg += "Error is on line %i. " % self.line_number
        if self.file_name:
            msg += "In file %s. " % self.file_name
        return msg

    @classmethod
    def from_task(
        cls,
        error_code: str,
        message: str,
        task: Task,
        status_code: int = 400,
        line_number: int = 0,
        offset: int = 0,
        error_type: str = "",
        error_line: str = "",
        task_trace: list | None = None,
    ) -> ApiError:
        """Constructs an API Error with details pulled from the current task."""
        instance = cls(error_code, message, status_code=status_code)
        instance.task_id = task.task_spec.name or ""
        instance.task_name = task.task_spec.description or ""
        instance.file_name = task.workflow.spec.file or ""
        instance.line_number = line_number
        instance.offset = offset
        instance.error_type = error_type
        instance.error_line = error_line
        if task_trace:
            instance.task_trace = task_trace
        else:
            instance.task_trace = WorkflowTaskException.get_task_trace(task)

        # spiffworkflow is doing something weird where task ends up referenced in the data in some cases.
        if "task" in task.data:
            task.data.pop("task")

        # Assure that there is nothing in the json data that can't be serialized.
        instance.task_data = ApiError.remove_unserializeable_from_dict(task.data)

        return instance

    @staticmethod
    def remove_unserializeable_from_dict(my_dict: dict) -> dict:
        """Removes unserializeable from dict."""
        keys_to_delete = []
        for key, value in my_dict.items():
            if not ApiError.is_jsonable(value):
                keys_to_delete.append(key)
        for key in keys_to_delete:
            del my_dict[key]
        return my_dict

    @staticmethod
    def is_jsonable(x: Any) -> bool:
        """Attempts a json.dump on given input and returns false if it cannot."""
        try:
            json.dumps(x)
            return True
        except (TypeError, OverflowError, ValueError):
            return False

    @classmethod
    def from_task_spec(
        cls,
        code: str,
        message: str,
        task_spec: TaskSpec,
        status_code: int = 400,
    ) -> ApiError:
        """Constructs an API Error with details pulled from the current task."""
        instance = cls(code, message, status_code=status_code)
        instance.task_id = task_spec.name or ""
        instance.task_name = task_spec.description or ""
        if task_spec._wf_spec:
            instance.file_name = task_spec._wf_spec.file
        return instance

    @classmethod
    def from_workflow_exception(
        cls,
        error_code: str,
        message: str,
        exp: SpiffWorkflowException,
    ) -> ApiError:
        """Deals with workflow exceptions.

        We catch a lot of workflow exception errors,
        so consolidating the error_code, and doing the best things
        we can with the data we have.
        """
        if isinstance(exp, WorkflowTaskException):
            # Note that WorkflowDataExceptions are also WorkflowTaskExceptions
            return ApiError.from_task(
                error_code,
                message,
                exp.task,
                line_number=exp.line_number,
                offset=exp.offset,
                error_type=exp.error_type,
                error_line=exp.error_line,
                task_trace=exp.task_trace,
            )
        elif isinstance(exp, WorkflowException):
            return ApiError.from_task_spec(error_code, message, exp.task_spec)
        else:
            return ApiError("workflow_error", str(exp))


def set_user_sentry_context() -> None:
    """Set_user_sentry_context."""
    try:
        username = g.user.username
    except Exception:
        username = "Unknown"
    # This is for sentry logging into Slack
    sentry_sdk.set_context("User", {"user": username})
    set_tag("username", username)


def should_notify_sentry(exception: Exception) -> bool:
    """Determine if we should notify sentry.

    We want to capture_exception to log the exception to sentry, but we don't want to log:
      1. ApiErrors that are just invalid tokens
      2. NotAuthorizedError. we usually call check-permissions before calling an API to
         make sure we'll have access, but there are some cases
         where it's more convenient to just make the call from the frontend and handle the 403 appropriately.
    """
    if isinstance(exception, ApiError):
        if exception.error_code == "invalid_token":
            return False
    if isinstance(exception, NotAuthorizedError):
        return False
    return True


@api_error_blueprint.app_errorhandler(Exception)  # type: ignore
def handle_exception(exception: Exception) -> flask.wrappers.Response:
    """Handles unexpected exceptions."""
    set_user_sentry_context()

    sentry_link = None
    if should_notify_sentry(exception):
        id = capture_exception(exception)

        if isinstance(exception, ApiError):
            current_app.logger.info(
                f"Sending ApiError exception to sentry: {exception} with error code"
                f" {exception.error_code}"
            )

        organization_slug = current_app.config.get("SPIFFWORKFLOW_BACKEND_SENTRY_ORGANIZATION_SLUG")
        project_slug = current_app.config.get("SPIFFWORKFLOW_BACKEND_SENTRY_PROJECT_SLUG")
        if organization_slug and project_slug:
            sentry_link = (
                f"https://sentry.io/{organization_slug}/{project_slug}/events/{id}"
            )

        # !!!NOTE!!!: do this after sentry stuff since calling logger.exception
        # seems to break the sentry sdk context where we no longer get back
        # an event id or send out tags like username
        current_app.logger.exception(exception)
    else:
        current_app.logger.warning(
            f"Received exception: {exception}. Since we do not want this particular"
            " exception in sentry, we cannot use logger.exception or logger.error, so"
            " there will be no backtrace. see api_error.py"
        )

    error_code = "internal_server_error"
    status_code = 500
    if (
        isinstance(exception, NotAuthorizedError)
        or isinstance(exception, TokenNotProvidedError)
        or isinstance(exception, TokenInvalidError)
    ):
        error_code = "not_authorized"
        status_code = 403
    if isinstance(exception, UserNotLoggedInError):
        error_code = "not_authenticated"
        status_code = 401

    # set api_exception like this to avoid confusing mypy
    # about what type the object is
    api_exception = None
    if isinstance(exception, ApiError):
        api_exception = exception
    elif isinstance(exception, SpiffWorkflowException):
        api_exception = ApiError.from_workflow_exception(
            "unexpected_workflow_exception", "Unexpected Workflow Error", exception
        )
    else:
        api_exception = ApiError(
            error_code=error_code,
            message=f"{exception.__class__.__name__}",
            sentry_link=sentry_link,
            status_code=status_code,
        )

    return make_response(jsonify(api_exception), api_exception.status_code)
