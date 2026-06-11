import copy
import json
import time
from typing import Any
from typing import cast

from flask import current_app
from SpiffWorkflow.bpmn.exceptions import WorkflowTaskException  # type: ignore
from SpiffWorkflow.spiff.specs.defaults import ServiceTask  # type: ignore
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore
from SpiffWorkflow.util.task import TaskState  # type: ignore

from spiffworkflow_backend.models.task import TaskModel
from spiffworkflow_backend.services.service_task_delegate import Accepted202Exception
from spiffworkflow_backend.services.service_task_delegate import ServiceTaskDelegate
from spiffworkflow_backend.services.service_task_delegate import logger


class RetryScheduledError(Exception):
    """Signals that a service task retry was scheduled and completion should be skipped."""


class CustomServiceTask(ServiceTask):  # type: ignore
    DEFAULT_RETRY_BACKOFF_BASE = 3
    RETRIES_ATTEMPTED_KEY = "spiff__retries_attempted"
    RETRY_AT_KEY = "spiff__retry_at"

    def __init__(
        self,
        *args: Any,
        retries: int | None = None,
        retry_backoff_base: int | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.retries = retries
        if retry_backoff_base is not None and int(retry_backoff_base) < 1:
            raise ValueError("retry_backoff_base must be a positive integer.")
        self.retry_backoff_base = int(retry_backoff_base) if retry_backoff_base is not None else None

    def _execute(self, spiff_task: SpiffTask) -> bool | None:
        def evaluate(param: dict) -> dict:
            param["value"] = spiff_task.workflow.script_engine.evaluate(spiff_task, param["value"])
            return param

        operation_params_copy = copy.deepcopy(self.operation_params)
        evaluated_params = {k: evaluate(v) for k, v in operation_params_copy.items()}

        try:
            result = spiff_task.workflow.script_engine.call_service(self.operation_name, evaluated_params, spiff_task)
        except Accepted202Exception:
            return None
        except Exception as e:
            if self.retries is not None and self.should_retry(spiff_task, e):
                self.schedule_retry(spiff_task)
                raise RetryScheduledError from None

            self.log_terminal_failure(spiff_task, e)
            wte = WorkflowTaskException("Error executing Service Task", task=spiff_task, exception=e)
            wte.add_note(str(e))
            raise wte from e

        parsed_result = json.loads(result)
        spiff_task.data[self.result_variable] = parsed_result

        self.clear_retry_state(spiff_task)

        return True

    def _run(self, spiff_task: SpiffTask) -> bool | None:
        try:
            return cast(bool | None, super()._run(spiff_task))
        except RetryScheduledError:
            spiff_task._set_state(TaskState.STARTED)
            raise

    def clear_retry_state(self, spiff_task: SpiffTask) -> None:
        spiff_task.internal_data.pop(self.RETRIES_ATTEMPTED_KEY, None)
        spiff_task.internal_data.pop(self.RETRY_AT_KEY, None)

    def get_retries_attempted(self, spiff_task: SpiffTask) -> int:
        retry_attempts = spiff_task.internal_data.get(self.RETRIES_ATTEMPTED_KEY)
        if retry_attempts is not None:
            normalized_retry_attempts = int(retry_attempts)
            spiff_task.internal_data[self.RETRIES_ATTEMPTED_KEY] = normalized_retry_attempts
            return normalized_retry_attempts
        return 0

    def consume_scheduled_retry(self, spiff_task: SpiffTask) -> None:
        spiff_task.internal_data[self.RETRIES_ATTEMPTED_KEY] = self.get_retries_attempted(spiff_task) + 1
        spiff_task.internal_data.pop(self.RETRY_AT_KEY, None)

    def get_process_instance_id(self, spiff_task: SpiffTask) -> Any:
        process_instance_id = None
        try:
            tld = current_app.config.get("THREAD_LOCAL_DATA")
            process_instance_id = getattr(tld, "process_instance_id", None)
        except RuntimeError:
            process_instance_id = None
        if process_instance_id is None:
            task_model = TaskModel.query.filter_by(guid=str(spiff_task.id)).first()
            if task_model is not None:
                process_instance_id = task_model.process_instance_id
        return process_instance_id

    def log_terminal_failure(self, spiff_task: SpiffTask, exception: Exception) -> None:
        retries_attempted = self.get_retries_attempted(spiff_task)
        retryable_error = ServiceTaskDelegate.is_transient_error(exception)
        retry_state = "not_retryable"
        if retryable_error:
            retry_state = "not_configured" if self.retries is None else "exhausted"
        logger.error(
            "Service Task '%s' failed and will not retry. "
            "process_instance_id=%s task_id=%s bpmn_id=%s retry_state=%s "
            "retryable_error=%s retries_attempted=%s max_retries=%s error_type=%s error=%s",
            self.operation_name,
            self.get_process_instance_id(spiff_task),
            spiff_task.id,
            self.bpmn_id,
            retry_state,
            retryable_error,
            retries_attempted,
            self.retries,
            exception.__class__.__name__,
            exception,
        )

    def should_retry(self, spiff_task: SpiffTask, exception: Exception) -> bool:
        if not ServiceTaskDelegate.is_transient_error(exception):
            return False
        if self.retries is None:
            return False

        return self.get_retries_attempted(spiff_task) < int(self.retries)

    def get_effective_retry_backoff_base(self) -> int:
        if self.retry_backoff_base is None:
            return self.DEFAULT_RETRY_BACKOFF_BASE
        return int(self.retry_backoff_base)

    def schedule_retry(self, spiff_task: SpiffTask) -> None:
        if self.retries is None:
            raise ValueError("Cannot schedule a retry without a configured retry count.")

        retries_attempted = self.get_retries_attempted(spiff_task)
        next_retry_number = retries_attempted + 1
        delay = self.get_effective_retry_backoff_base() ** next_retry_number
        run_at = round(time.time() + delay)

        logger.warning(
            "Service Task '%s' failed and will retry. "
            "process_instance_id=%s task_id=%s bpmn_id=%s next_retry_number=%s "
            "max_retries=%s retries_attempted=%s retries_remaining=%s retry_at=%s delay_seconds=%s",
            self.operation_name,
            self.get_process_instance_id(spiff_task),
            spiff_task.id,
            self.bpmn_id,
            next_retry_number,
            self.retries,
            retries_attempted,
            max(int(self.retries) - retries_attempted, 0),
            run_at,
            delay,
        )

        spiff_task.internal_data[self.RETRIES_ATTEMPTED_KEY] = retries_attempted
        spiff_task.internal_data[self.RETRY_AT_KEY] = run_at

        # Return None to indicate the task is still in progress (STARTED).
        return None
