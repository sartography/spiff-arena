import copy
import json

from SpiffWorkflow.bpmn.exceptions import WorkflowTaskException  # type: ignore
from SpiffWorkflow.spiff.specs.defaults import ServiceTask  # type: ignore
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore

from spiffworkflow_backend.services.service_task_delegate import Accepted202Exception
from spiffworkflow_backend.services.service_task_delegate import logger


class CustomServiceTask(ServiceTask):  # type: ignore
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
            logger.exception("Error executing Service Task '%s': %s", self.operation_name, str(e))
            wte = WorkflowTaskException("Error executing Service Task", task=spiff_task, exception=e)
            wte.add_note(str(e))
            raise wte from e

        parsed_result = json.loads(result)
        spiff_task.data[self.result_variable] = parsed_result

        return True
