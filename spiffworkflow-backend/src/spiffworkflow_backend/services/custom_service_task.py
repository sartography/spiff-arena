import copy
import json
import time
from typing import Any

from SpiffWorkflow.bpmn.exceptions import WorkflowTaskException  # type: ignore
from SpiffWorkflow.spiff.specs.defaults import ServiceTask  # type: ignore
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore

from spiffworkflow_backend.services.service_task_delegate import Accepted202Exception
from spiffworkflow_backend.services.service_task_delegate import logger


class CustomServiceTask(ServiceTask):  # type: ignore
    def __init__(self, *args: Any, retries: int | None = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.retries = retries

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
                return None

            logger.exception("Error executing Service Task '%s': %s", self.operation_name, str(e))
            wte = WorkflowTaskException("Error executing Service Task", task=spiff_task, exception=e)
            wte.add_note(str(e))
            raise wte from e

        parsed_result = json.loads(result)
        spiff_task.data[self.result_variable] = parsed_result

        # If we succeeded, clear the retry counter if it exists
        spiff_task.internal_data.pop("spiff__retry_count", None)
        spiff_task.internal_data.pop("spiff__retry_at", None)

        return True

    def should_retry(self, spiff_task: SpiffTask, exception: Exception) -> bool:
        from spiffworkflow_backend.services.service_task_delegate import ServiceTaskDelegate

        if not ServiceTaskDelegate.is_transient_error(exception):
            return False

        # Check retry counter
        retry_count = spiff_task.internal_data.get("spiff__retry_count", self.retries)
        return int(retry_count) > 0

    def schedule_retry(self, spiff_task: SpiffTask) -> None:
        if self.retries is None:
            raise ValueError("Cannot schedule a retry without a configured retry count.")
        current_retry = spiff_task.internal_data.get("spiff__retry_count", self.retries)
        next_retry = int(current_retry) - 1
        spiff_task.internal_data["spiff__retry_count"] = next_retry

        # Exponential backoff: 2s, 4s, 8s, 16s, ...
        attempt_number = int(self.retries) - int(current_retry)
        delay = 2 ** (attempt_number + 1)
        run_at = round(time.time() + delay)

        logger.info(
            f"Scheduling retry for Service Task '{self.operation_name}' (task_id: {spiff_task.id}). "
            f"Remaining retries: {next_retry}. Backoff delay: {delay}s."
        )

        spiff_task.internal_data["spiff__retry_at"] = run_at

        # Return None to indicate the task is still in progress (STARTED).
        return None
