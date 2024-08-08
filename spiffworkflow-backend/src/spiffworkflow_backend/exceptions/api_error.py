"""API Error functionality."""

from __future__ import annotations

import json
from dataclasses import dataclass
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
from SpiffWorkflow.bpmn.exceptions import WorkflowTaskException  # type: ignore
from SpiffWorkflow.exceptions import SpiffWorkflowException  # type: ignore
from SpiffWorkflow.exceptions import WorkflowException
from SpiffWorkflow.specs.base import TaskSpec  # type: ignore
from SpiffWorkflow.task import Task  # type: ignore
from spiffworkflow_backend.exceptions.error import NotAuthorizedError
from spiffworkflow_backend.exceptions.error import TokenInvalidError
from spiffworkflow_backend.exceptions.error import TokenNotProvidedError
from spiffworkflow_backend.exceptions.error import UserNotLoggedInError
from spiffworkflow_backend.models.task import TaskModel  # noqa: F401
from spiffworkflow_backend.services.task_service import TaskModelError
from spiffworkflow_backend.services.task_service import TaskService
from werkzeug.exceptions import MethodNotAllowed

api_error_blueprint = Blueprint("api_error_blueprint", __name__)


@dataclass
class ApiError(Exception):
    """ApiError Class to help handle exceptions."""

    error_code: str
    message: str
    error_line: str | None = None
    error_type: str | None = None
    file_name: str | None = None
    line_number: int | None = None
    offset: int | None = None
    sentry_link: str | None = None
    status_code: int | None = 400
    tag: str | None = None
    task_data: dict | str | None = None
    task_id: str | None = None
    task_name: str | None = None
    task_trace: list | None = None

    # these are useful if the error response cannot be json but has to be something else
    # such as returning content type 'text/event-stream' for the interstitial page
    response_headers: dict | None = None
    response_message: str | None = None

    def __str__(self) -> str:
        """Instructions to print instance as a string."""
        msg = "ApiError: % s. " % self.message  # noqa: UP031
        if self.task_name:
            msg += f"Error in task '{self.task_name}' ({self.task_id}). "
        if self.line_number:
            msg += "Error is on line %i. " % self.line_number
        if self.file_name:
            msg += f"In file {self.file_name}. "
        return msg

    def serialized(self) -> dict[str, Any]:
        initial_dict = self.__dict__
        return_dict = {}
        for key, value in initial_dict.items():
            if value is not None and value != "":
                return_dict[key] = value
        return return_dict

    @classmethod
    def from_task(
        cls,
        error_code: str,
        message: str,
        task: Task,
        status_code: int = 400,
        line_number: int | None = None,
        offset: int | None = None,
        error_type: str | None = None,
        error_line: str | None = None,
        task_trace: list | None = None,
    ) -> ApiError:
        """Constructs an API Error with details pulled from the current task."""
        instance = cls(error_code, message, status_code=status_code)
        instance.task_id = task.task_spec.name
        instance.task_name = task.task_spec.description
        instance.file_name = task.workflow.spec.file
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

    @classmethod
    def from_task_model(
        cls,
        error_code: str,
        message: str,
        task_model: TaskModel,
        status_code: int | None = 400,
        line_number: int | None = None,
        offset: int | None = None,
        error_type: str | None = None,
        error_line: str | None = None,
        task_trace: list | None = None,
    ) -> ApiError:
        """Constructs an API Error with details pulled from the current task model."""
        instance = cls(error_code, message, status_code=status_code)
        task_definition = task_model.task_definition
        instance.task_id = task_definition.bpmn_identifier
        instance.task_name = task_definition.bpmn_name
        instance.line_number = line_number
        instance.offset = offset
        instance.error_type = error_type
        instance.error_line = error_line
        if task_trace:
            instance.task_trace = task_trace
        else:
            instance.task_trace = TaskModelError.get_task_trace(task_model)

        try:
            spec_reference_filename = TaskService.get_spec_filename_from_bpmn_process(task_model.bpmn_process)
            instance.file_name = spec_reference_filename
        except Exception as exception:
            current_app.logger.error(exception)

        # Assure that there is nothing in the json data that can't be serialized.
        instance.task_data = ApiError.remove_unserializeable_from_dict(task_model.get_data())

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
        if hasattr(task_spec, "_wf_spec") and task_spec._wf_spec:
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
                message + ". " + str(exp),
                exp.task,
                line_number=exp.line_number,
                offset=exp.offset,
                error_type=exp.error_type,
                error_line=exp.error_line,
                task_trace=exp.task_trace,
            )
        elif isinstance(exp, TaskModelError):
            # Note that WorkflowDataExceptions are also WorkflowTaskExceptions
            return ApiError.from_task_model(
                error_code,
                message + ". " + str(exp),
                exp.task_model,
                line_number=exp.line_number,
                offset=exp.offset,
                error_type=exp.error_type,
                error_line=exp.error_line,
                task_trace=exp.task_trace,
            )
        elif isinstance(exp, WorkflowException) and exp.task_spec:
            msg = message + ". " + str(exp)
            return ApiError.from_task_spec(error_code, msg, exp.task_spec)
        else:
            return ApiError("workflow_error", str(exp))


def set_user_sentry_context() -> None:
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
      1. ApiErrors that we expect to happen and that don't indicate bugs
      2. NotAuthorizedError. we usually call check-permissions before calling an API to
         make sure we'll have access, but there are some cases
         where it's more convenient to just make the call from the frontend and handle the 403 appropriately.
    """
    if isinstance(exception, ApiError):
        if exception.error_code == "invalid_token":
            return False
        # when someone is looking for a process instance that doesn't exist or that they don't have access to
        if exception.error_code == "process_instance_cannot_be_found":
            return False
    if isinstance(exception, NotAuthorizedError):
        return False

    # like a 404, 405 Method Not Allowed: The method is not allowed for the requested URL
    # it doesn't seem to work to exclude this here. i guess it happens before it gets to our app?
    # excluded via before_send in configure_sentry
    if isinstance(exception, MethodNotAllowed):
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
            current_app.logger.info(f"Sending ApiError exception to sentry: {exception} with error code {exception.error_code}")

        organization_slug = current_app.config.get("SPIFFWORKFLOW_BACKEND_SENTRY_ORGANIZATION_SLUG")
        project_slug = current_app.config.get("SPIFFWORKFLOW_BACKEND_SENTRY_PROJECT_SLUG")
        if organization_slug and project_slug:
            sentry_link = f"https://sentry.io/{organization_slug}/{project_slug}/events/{id}"

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
    if isinstance(exception, NotAuthorizedError | TokenNotProvidedError | TokenInvalidError):
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
        api_exception = ApiError.from_workflow_exception("unexpected_workflow_exception", "Unexpected Workflow Error", exception)
    else:
        api_exception = ApiError(
            error_code=error_code,
            message=f"{exception.__class__.__name__}: {str(exception)}",
            sentry_link=sentry_link,
            status_code=status_code,
        )

    response_message = api_exception.response_message
    if response_message is None:
        response_message = jsonify(api_exception)

    error_response = make_response(response_message, api_exception.status_code)
    if api_exception.response_headers is not None:
        for header, value in api_exception.response_headers.items():
            error_response.headers[header] = value
    return error_response
