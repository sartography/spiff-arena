"""API Error functionality."""
from __future__ import annotations

import json
from typing import Any

import sentry_sdk
from flask import Blueprint
from flask import current_app
from flask import g
from marshmallow import Schema
from SpiffWorkflow.bpmn.exceptions import WorkflowTaskExecException  # type: ignore
from SpiffWorkflow.exceptions import WorkflowException  # type: ignore
from SpiffWorkflow.specs.base import TaskSpec  # type: ignore
from SpiffWorkflow.task import Task  # type: ignore
from werkzeug.exceptions import InternalServerError

api_error_blueprint = Blueprint("api_error_blueprint", __name__)


class ApiError(Exception):
    """ApiError Class to help handle exceptions."""

    def __init__(
        self,
        error_code: str,
        message: str,
        status_code: int = 400,
        file_name: str = "",
        task_id: str = "",
        task_name: str = "",
        tag: str = "",
        task_data: dict | None | str = None,
        error_type: str = "",
        error_line: str = "",
        line_number: int = 0,
        offset: int = 0,
        task_trace: dict | None = None,
    ) -> None:
        """The Init Method."""
        if task_data is None:
            task_data = {}
        if task_trace is None:
            task_trace = {}
        self.status_code = status_code
        self.error_code = error_code  # a short consistent string describing the error.
        self.message = message  # A detailed message that provides more information.

        # OPTIONAL:  The id of the task in the BPMN Diagram.
        self.task_id = task_id or ""

        # OPTIONAL: The name of the task in the BPMN Diagram.

        # OPTIONAL: The file that caused the error.
        self.task_name = task_name or ""
        self.file_name = file_name or ""

        # OPTIONAL: The XML Tag that caused the issue.
        self.tag = tag or ""

        # OPTIONAL: A snapshot of data connected to the task when error occurred.
        self.task_data = task_data or ""
        self.line_number = line_number
        self.offset = offset
        self.error_type = error_type
        self.error_line = error_line
        self.task_trace = task_trace

        try:
            user = g.user.uid
        except Exception:
            user = "Unknown"
        self.task_user = user
        # This is for sentry logging into Slack
        sentry_sdk.set_context("User", {"user": user})
        Exception.__init__(self, self.message)

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


class ApiErrorSchema(Schema):
    """ApiErrorSchema Class."""

    class Meta:
        """Sets the fields to search the error schema for."""

        fields = (
            "error_code",
            "message",
            "workflow_name",
            "file_name",
            "task_name",
            "task_id",
            "task_data",
            "task_user",
            "hint",
            "line_number",
            "offset",
            "error_type",
            "error_line",
            "task_trace",
        )


@api_error_blueprint.app_errorhandler(ApiError)
def handle_invalid_usage(error: ApiError) -> tuple[str, int]:
    """Handles invalid usage error."""
    response = ApiErrorSchema().dump(error)
    return response, error.status_code


@api_error_blueprint.app_errorhandler(InternalServerError)
def handle_internal_server_error(error: InternalServerError) -> tuple[str, int]:
    """Handles internal server error."""
    original = getattr(error, "original_exception", None)
    api_error = ApiError(
        error_code="Internal Server Error (500)", message=str(original)
    )
    response = ApiErrorSchema().dump(api_error)
    return response, 500
