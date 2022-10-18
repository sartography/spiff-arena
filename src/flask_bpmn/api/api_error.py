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
from sentry_sdk import set_user
from SpiffWorkflow.bpmn.exceptions import WorkflowTaskExecException  # type: ignore
from SpiffWorkflow.exceptions import WorkflowException  # type: ignore
from SpiffWorkflow.specs.base import TaskSpec  # type: ignore
from SpiffWorkflow.task import Task  # type: ignore
from werkzeug.exceptions import InternalServerError


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
    task_trace: dict | None = field(default_factory=dict)

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
        task_trace: dict | None = None,
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
            instance.task_trace = WorkflowTaskExecException.get_task_trace(task)

        # spiffworkflow is doing something weird where task ends up referenced in the data in some cases.
        if "task" in task.data:
            task.data.pop("task")

        # Assure that there is nothing in the json data that can't be serialized.
        instance.task_data = ApiError.remove_unserializeable_from_dict(task.data)

        current_app.logger.error(message, exc_info=True)
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
        current_app.logger.error(message, exc_info=True)
        return instance

    @classmethod
    def from_workflow_exception(
        cls,
        error_code: str,
        message: str,
        exp: WorkflowException,
    ) -> ApiError:
        """Deals with workflow exceptions.

        We catch a lot of workflow exception errors,
        so consolidating the error_code, and doing the best things
        we can with the data we have.
        """
        if isinstance(exp, WorkflowTaskExecException):
            return ApiError.from_task(
                error_code,
                message,
                exp.task,
                line_number=exp.line_number,
                offset=exp.offset,
                error_type=exp.exception.__class__.__name__,
                error_line=exp.error_line,
                task_trace=exp.task_trace,
            )

        else:
            return ApiError.from_task_spec(error_code, message, exp.sender)


def set_user_sentry_context() -> None:
    """Set_user_sentry_context."""
    try:
        username = g.user.username
    except Exception:
        username = "Unknown"
    # This is for sentry logging into Slack
    sentry_sdk.set_context("User", {"user": username})
    set_user({"username": username})


@api_error_blueprint.app_errorhandler(ApiError)
def handle_invalid_usage(error: ApiError) -> flask.wrappers.Response:
    """Handles invalid usage error."""
    return make_response(jsonify(error), error.status_code)


@api_error_blueprint.app_errorhandler(InternalServerError)
def handle_internal_server_error(error: InternalServerError) -> flask.wrappers.Response:
    """Handles internal server error."""
    original = getattr(error, "original_exception", None)
    api_error = ApiError(error_code="internal_server_error", message=str(original))
    return make_response(jsonify(api_error), 500)


@api_error_blueprint.app_errorhandler(Exception)
def handle_internal_server_exception(exception: Exception) -> flask.wrappers.Response:
    """Handles unexpected exceptions."""
    set_user_sentry_context()
    id = capture_exception(exception)

    organization_slug = current_app.config.get("SENTRY_ORGANIZATION_SLUG")
    project_slug = current_app.config.get("SENTRY_PROJECT_SLUG")
    sentry_link = None
    if organization_slug and project_slug:
        sentry_link = (
            f"https://sentry.io/{organization_slug}/{project_slug}/events/{id}"
        )

    api_exception = ApiError(
        error_code="error",
        message=f"{exception.__class__.__name__}",
        sentry_link=sentry_link,
    )
    return make_response(jsonify(api_exception), 500)
