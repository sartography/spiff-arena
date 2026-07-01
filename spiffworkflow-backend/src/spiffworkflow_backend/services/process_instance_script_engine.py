import _strptime  # type: ignore
import calendar
import decimal
import json
import os
import random
import re
import time
import uuid
from collections.abc import Callable
from datetime import datetime
from datetime import timedelta
from typing import Any

import dateparser
import pytz
from flask import current_app
from RestrictedPython import safe_globals  # type: ignore
from SpiffWorkflow.bpmn.exceptions import WorkflowTaskException  # type: ignore
from SpiffWorkflow.bpmn.script_engine import BasePythonScriptEngineEnvironment  # type: ignore
from SpiffWorkflow.bpmn.script_engine import PythonScriptEngine
from SpiffWorkflow.bpmn.script_engine import TaskDataEnvironment
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow  # type: ignore
from SpiffWorkflow.exceptions import WorkflowException  # type: ignore
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore

from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.script import Script
from spiffworkflow_backend.services.jinja_service import JinjaHelpers
from spiffworkflow_backend.services.service_task_delegate import ServiceTaskDelegate


def _import(name: str, glbls: dict[str, Any], *args: Any) -> Any:
    if name not in glbls:
        raise ImportError(f"Import not allowed: {name}", name=name)
    return glbls[name]


class BaseCustomScriptEngineEnvironment(BasePythonScriptEngineEnvironment):  # type: ignore
    def user_defined_state(self, external_context: dict[str, Any] | None = None) -> dict[str, Any]:
        return {}

    def last_result(self) -> dict[str, Any]:
        return dict(self._last_result.items())

    def clear_state(self) -> None:
        pass

    def pop_state(self, data: dict[str, Any]) -> dict[str, Any]:
        return {}

    def preserve_state(self, bpmn_process_instance: BpmnWorkflow) -> None:
        pass

    def restore_state(self, bpmn_process_instance: BpmnWorkflow) -> None:
        pass

    def finalize_result(self, bpmn_process_instance: BpmnWorkflow) -> None:
        pass

    def revise_state_with_task_data(self, task: SpiffTask) -> None:
        pass


class TaskDataBasedScriptEngineEnvironment(BaseCustomScriptEngineEnvironment, TaskDataEnvironment):  # type: ignore
    def __init__(self, environment_globals: dict[str, Any]):
        self._last_result: dict[str, Any] = {}
        self._non_user_defined_keys = {"__annotations__"}
        super().__init__(environment_globals)

    def execute(
        self,
        script: str,
        context: dict[str, Any],
        external_context: dict[str, Any] | None = None,
    ) -> bool:
        super().execute(script, context, external_context)
        for key in self._non_user_defined_keys:
            if key in context:
                context.pop(key)
        self._last_result = context
        return True


class NonTaskDataBasedScriptEngineEnvironment(BaseCustomScriptEngineEnvironment):
    PYTHON_ENVIRONMENT_STATE_KEY = "spiff__python_env_state"

    def __init__(self, environment_globals: dict[str, Any]):
        self.state: dict[str, Any] = {}
        self.non_user_defined_keys = set([*environment_globals.keys()] + ["__builtins__", "__annotations__"])
        super().__init__(environment_globals)

    def evaluate(
        self,
        expression: str,
        context: dict[str, Any],
        external_context: dict[str, Any] | None = None,
    ) -> Any:
        state = {}
        state.update(self.globals)
        state.update(external_context or {})
        state.update(self.state)
        state.update(context)
        return eval(expression, state)  # noqa

    def execute(
        self,
        script: str,
        context: dict[str, Any],
        external_context: dict[str, Any] | None = None,
    ) -> bool:
        self.state.update(self.globals)
        self.state.update(external_context or {})
        self.state.update(context)
        try:
            exec(script, self.state)  # noqa
            return True
        finally:
            context_keys_to_drop = context.keys() - self.state.keys()

            for key_to_drop in context_keys_to_drop:
                context.pop(key_to_drop)

            self.state = self.user_defined_state(external_context)
            context.update(self.state)

    def user_defined_state(self, external_context: dict[str, Any] | None = None) -> dict[str, Any]:
        keys_to_filter = set(self.non_user_defined_keys)
        if external_context is not None:
            keys_to_filter |= set(external_context.keys())

        return {k: v for k, v in self.state.items() if k not in keys_to_filter and not callable(v)}

    def last_result(self) -> dict[str, Any]:
        return dict(self.state.items())

    def clear_state(self) -> None:
        self.state = {}

    def pop_state(self, data: dict[str, Any]) -> dict[str, Any]:
        key = self.PYTHON_ENVIRONMENT_STATE_KEY
        return data.pop(key, {})  # type: ignore

    def preserve_state(self, bpmn_process_instance: BpmnWorkflow) -> None:
        key = self.PYTHON_ENVIRONMENT_STATE_KEY
        state = self.user_defined_state()
        bpmn_process_instance.data[key] = state

    def restore_state(self, bpmn_process_instance: BpmnWorkflow) -> None:
        key = self.PYTHON_ENVIRONMENT_STATE_KEY
        self.state = bpmn_process_instance.data.get(key, {})

    def finalize_result(self, bpmn_process_instance: BpmnWorkflow) -> None:
        bpmn_process_instance.data.update(self.user_defined_state())

    def revise_state_with_task_data(self, task: SpiffTask) -> None:
        state_keys = set(self.state.keys())
        task_data_keys = set(task.data.keys())
        state_keys_to_remove = state_keys - task_data_keys
        task_data_keys_to_keep = task_data_keys - state_keys

        self.state = {k: v for k, v in self.state.items() if k not in state_keys_to_remove}
        task.data = {k: v for k, v in task.data.items() if k in task_data_keys_to_keep}

        if hasattr(task.task_spec, "_result_variable"):
            result_variable = task.task_spec._result_variable(task)
            if result_variable in task.data:
                self.state[result_variable] = task.data.pop(result_variable)


class CustomScriptEngineEnvironment:
    @staticmethod
    def create(environment_globals: dict[str, Any]) -> BaseCustomScriptEngineEnvironment:
        if os.environ.get("SPIFFWORKFLOW_BACKEND_USE_NON_TASK_DATA_BASED_SCRIPT_ENGINE_ENVIRONMENT") == "true":
            return NonTaskDataBasedScriptEngineEnvironment(environment_globals)

        return TaskDataBasedScriptEngineEnvironment(environment_globals)


class CustomBpmnScriptEngine(PythonScriptEngine):  # type: ignore
    """Custom SpiffWorkflow script engine for Arena process execution."""

    def __init__(self, use_restricted_script_engine: bool = True) -> None:
        default_globals = {
            "_strptime": _strptime,
            "all": all,
            "any": any,
            "calendar": calendar,
            "dateparser": dateparser,
            "datetime": datetime,
            "decimal": decimal,
            "dict": dict,
            "enumerate": enumerate,
            "filter": filter,
            "format": format,
            "json": json,
            "list": list,
            "map": map,
            "max": max,
            "min": min,
            "pytz": pytz,
            "random": random,
            "re": re,
            "set": set,
            "sum": sum,
            "time": time,
            "timedelta": timedelta,
            "uuid": uuid,
            **JinjaHelpers.get_helper_mapping(),
        }

        if os.environ.get("SPIFFWORKFLOW_BACKEND_USE_RESTRICTED_SCRIPT_ENGINE") == "false":
            use_restricted_script_engine = False

        if use_restricted_script_engine:
            default_globals.update(safe_globals)
            default_globals["__builtins__"]["__import__"] = _import

        environment = CustomScriptEngineEnvironment.create(default_globals)
        super().__init__(environment=environment)

    def __get_process_instance_id(self) -> Any | None:
        tld = current_app.config.get("THREAD_LOCAL_DATA")
        process_instance_id = None
        if tld:
            if hasattr(tld, "process_instance_id"):
                process_instance_id = tld.process_instance_id
        return process_instance_id

    def __get_process_model_identifier(self) -> Any | None:
        tld = current_app.config.get("THREAD_LOCAL_DATA")
        process_model_identifier = None
        if tld:
            if hasattr(tld, "process_model_identifier"):
                process_model_identifier = tld.process_model_identifier
        return process_model_identifier

    def __get_augment_methods(self, task: SpiffTask | None) -> dict[str, Callable]:
        script_attributes_context = ScriptAttributesContext(
            task=task,
            environment_identifier=current_app.config["ENV_IDENTIFIER"],
            process_instance_id=self.__get_process_instance_id(),
            process_model_identifier=self.__get_process_model_identifier(),
        )
        return Script.generate_augmented_list(script_attributes_context)

    def evaluate(self, task: SpiffTask, expression: str, external_context: dict[str, Any] | None = None) -> Any:
        methods = self.__get_augment_methods(task)
        if external_context:
            methods.update(external_context)

        try:
            return super().evaluate(task, expression, external_context=methods)
        except Exception as exception:
            if task is None:
                raise WorkflowException(
                    f"Error evaluating expression: '{expression}', {str(exception)}",
                ) from exception
            else:
                raise WorkflowTaskException(
                    f"Error evaluating expression '{expression}', {str(exception)}",
                    task=task,
                    exception=exception,
                ) from exception

    def execute(self, task: SpiffTask, script: str, external_context: Any = None) -> bool:
        try:
            methods = self.__get_augment_methods(task)
            if external_context:
                methods.update(external_context)

            task_name = task.task_spec.bpmn_name if hasattr(task.task_spec, "bpmn_name") else task.task_spec.name
            task_id = str(task.id)
            current_app.logger.debug(f"SCRIPT TASK EXECUTION - START: {task_name} (ID: {task_id})")

            if script:
                current_app.logger.debug(f"SCRIPT TASK EXECUTION - Running script for: {task_name} (ID: {task_id})")
                super().execute(task, script, methods)
                current_app.logger.debug(f"SCRIPT TASK EXECUTION - COMPLETED: {task_name} (ID: {task_id})")
            return True
        except WorkflowException:
            raise
        except Exception as e:
            raise self.create_task_exec_exception(task, script, e) from e

    def call_service(
        self,
        operation_name: str,
        operation_params: dict[str, Any],
        spiff_task: SpiffTask,
    ) -> str:
        return ServiceTaskDelegate.call_connector(
            operation_name,
            operation_params,
            spiff_task,
            self.__get_process_instance_id(),
            self.__get_process_model_identifier(),
        )
