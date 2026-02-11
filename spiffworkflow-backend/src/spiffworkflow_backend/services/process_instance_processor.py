# TODO: clean up this service for a clear distinction between it and the process_instance_service
#   where this points to the pi service
import _strptime  # type: ignore
import calendar
import copy
import decimal
import json
import logging
import os
import random
import re
import time
import uuid
from collections.abc import Callable
from contextlib import suppress
from datetime import datetime
from datetime import timedelta
from typing import Any
from typing import NewType
from uuid import UUID
from uuid import uuid4

import dateparser
import pytz
from flask import current_app
from RestrictedPython import safe_globals  # type: ignore
from SpiffWorkflow.bpmn import BpmnEvent  # type: ignore
from SpiffWorkflow.bpmn.exceptions import WorkflowTaskException  # type: ignore
from SpiffWorkflow.bpmn.script_engine import BasePythonScriptEngineEnvironment  # type: ignore
from SpiffWorkflow.bpmn.script_engine import PythonScriptEngine
from SpiffWorkflow.bpmn.script_engine import TaskDataEnvironment
from SpiffWorkflow.bpmn.serializer.helpers.registry import DefaultRegistry  # type: ignore
from SpiffWorkflow.bpmn.specs.bpmn_process_spec import BpmnProcessSpec  # type: ignore
from SpiffWorkflow.bpmn.util.diff import WorkflowDiff  # type: ignore
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow  # type: ignore
from SpiffWorkflow.exceptions import WorkflowException  # type: ignore
from SpiffWorkflow.serializer.exceptions import MissingSpecError  # type: ignore
from SpiffWorkflow.spiff.specs.defaults import ServiceTask  # type: ignore

# fix for StandardLoopTask
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore
from SpiffWorkflow.util.deep_merge import DeepMerge  # type: ignore
from SpiffWorkflow.util.task import TaskIterator  # type: ignore
from SpiffWorkflow.util.task import TaskState
from sqlalchemy import and_
from sqlalchemy import or_

from spiffworkflow_backend.background_processing.celery_tasks.process_instance_task_producer import (
    queue_event_notifier_if_appropriate,
)
from spiffworkflow_backend.constants import SPIFFWORKFLOW_BACKEND_SERIALIZER_VERSION
from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.exceptions.error import TaskMismatchError
from spiffworkflow_backend.interfaces import PotentialOwner
from spiffworkflow_backend.interfaces import PotentialOwnerIdList
from spiffworkflow_backend.models.bpmn_process import BpmnProcessModel
from spiffworkflow_backend.models.bpmn_process_definition import BpmnProcessDefinitionModel

# noqa: F401
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.future_task import FutureTaskModel
from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.human_task_user import HumanTaskUserAddedBy
from spiffworkflow_backend.models.human_task_user import HumanTaskUserModel
from spiffworkflow_backend.models.json_data import JsonDataModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceCannotBeRunError
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
from spiffworkflow_backend.models.process_instance_event import ProcessInstanceEventType
from spiffworkflow_backend.models.process_instance_metadata import ProcessInstanceMetadataModel
from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.models.task import TaskModel
from spiffworkflow_backend.models.task import TaskNotFoundError
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.scripts.script import Script
from spiffworkflow_backend.services.bpmn_process_service import BpmnProcessService
from spiffworkflow_backend.services.jinja_service import JinjaHelpers
from spiffworkflow_backend.services.logging_service import LoggingService
from spiffworkflow_backend.services.process_instance_queue_service import ProcessInstanceQueueService
from spiffworkflow_backend.services.process_instance_tmp_service import ProcessInstanceTmpService
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.service_task_service import ServiceTaskDelegate
from spiffworkflow_backend.services.task_service import StartAndEndTimes
from spiffworkflow_backend.services.task_service import TaskService
from spiffworkflow_backend.services.user_service import UserService
from spiffworkflow_backend.services.workflow_execution_service import ExecutionStrategy
from spiffworkflow_backend.services.workflow_execution_service import ExecutionStrategyNotConfiguredError
from spiffworkflow_backend.services.workflow_execution_service import SkipOneExecutionStrategy
from spiffworkflow_backend.services.workflow_execution_service import TaskModelSavingDelegate
from spiffworkflow_backend.services.workflow_execution_service import TaskRunnability
from spiffworkflow_backend.services.workflow_execution_service import WorkflowExecutionService
from spiffworkflow_backend.services.workflow_execution_service import execution_strategy_named
from spiffworkflow_backend.services.workflow_spec_service import IdToBpmnProcessSpecMapping

# Sorry about all this crap.  I wanted to move this thing to another file, but
# importing a bunch of types causes circular imports.

WorkflowCompletedHandler = Callable[[ProcessInstanceModel], None]


def _import(name: str, glbls: dict[str, Any], *args: Any) -> None:
    if name not in glbls:
        raise ImportError(f"Import not allowed: {name}", name=name)


# This number is a little arbitrary but seems like a good number.
MAX_PROCESS_INSTANCE_TASK_COUNT = 20000


class ProcessInstanceTaskCountExceededError(Exception):
    """This error is raised if too many tasks were generated.

    Too many tasks is defined as enough tasks to take down the system such as 700,000.
    These tasks will generally be predicted tasks that are never actually run and just bloat the instance.
    These are largely created when using multiple parallel gateways and current recommended fix is to put in subprocesses.
    """


class ProcessInstanceProcessorError(Exception):
    pass


class NoPotentialOwnersForTaskError(Exception):
    pass


class PotentialOwnerUserNotFoundError(Exception):
    pass


class MissingProcessInfoError(Exception):
    pass


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
            # since the task data is not directly mutated when the script executes, need to determine which keys
            # have been deleted from the environment and remove them from task data if present.
            context_keys_to_drop = context.keys() - self.state.keys()

            for key_to_drop in context_keys_to_drop:
                context.pop(key_to_drop)

            self.state = self.user_defined_state(external_context)

            # the task data needs to be updated with the current state so data references can be resolved properly.
            # the state will be removed later once the task is completed.
            context.update(self.state)

    def user_defined_state(self, external_context: dict[str, Any] | None = None) -> dict[str, Any]:
        keys_to_filter = self.non_user_defined_keys
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
    """This is a custom script processor that can be easily injected into Spiff Workflow.

    It will execute python code read in from the bpmn.  It will also make any scripts in the
    scripts directory available for execution.
    """

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
            # This will overwrite the standard builtins
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
        """Evaluate the given expression, within the context of the given task and return the result."""
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
            # reset failing task just in case
            methods = self.__get_augment_methods(task)
            if external_context:
                methods.update(external_context)

            # Debug logs for script execution
            task_name = task.task_spec.bpmn_name if hasattr(task.task_spec, "bpmn_name") else task.task_spec.name
            task_id = str(task.id)
            current_app.logger.debug(f"SCRIPT TASK EXECUTION - START: {task_name} (ID: {task_id})")

            # do not run script if it is blank
            if script:
                current_app.logger.debug(f"SCRIPT TASK EXECUTION - Running script for: {task_name} (ID: {task_id})")
                super().execute(task, script, methods)
                current_app.logger.debug(f"SCRIPT TASK EXECUTION - COMPLETED: {task_name} (ID: {task_id})")
            return True
        except WorkflowException as e:
            current_app.logger.error(f"SCRIPT TASK EXECUTION - WORKFLOW EXCEPTION: {str(e)}")
            raise e
        except Exception as e:
            current_app.logger.error(f"SCRIPT TASK EXECUTION - EXCEPTION: {str(e)}")
            raise self.create_task_exec_exception(task, script, e) from e

    def call_service(
        self,
        operation_name: str,
        operation_params: dict[str, Any],
        spiff_task: SpiffTask,
    ) -> str:
        return ServiceTaskDelegate.call_connector(operation_name, operation_params, spiff_task, self.__get_process_instance_id())


SubprocessUuidToWorkflowDiffMapping = NewType("SubprocessUuidToWorkflowDiffMapping", dict[UUID, WorkflowDiff])


class ProcessInstanceProcessor:
    _default_script_engine = CustomBpmnScriptEngine()

    PROCESS_INSTANCE_ID_KEY = "process_instance_id"

    # __init__ calls these helpers:
    #   * get_spec, which returns a spec and any subprocesses (as IdToBpmnProcessSpecMapping dict)
    #   * __get_bpmn_process_instance, which takes spec and subprocesses and instantiates and returns a BpmnWorkflow
    def __init__(
        self,
        process_instance_model: ProcessInstanceModel,
        script_engine: PythonScriptEngine | None = None,
        workflow_completed_handler: WorkflowCompletedHandler | None = None,
        process_id_to_run: str | None = None,
        include_task_data_for_completed_tasks: bool = False,
        include_completed_subprocesses: bool = False,
    ) -> None:
        """Create a Workflow Processor based on the serialized information available in the process_instance model."""
        self._script_engine = script_engine or self.__class__._default_script_engine
        self._workflow_completed_handler = workflow_completed_handler
        self.setup_processor_with_process_instance(
            process_instance_model=process_instance_model,
            process_id_to_run=process_id_to_run,
            include_task_data_for_completed_tasks=include_task_data_for_completed_tasks,
            include_completed_subprocesses=include_completed_subprocesses,
        )

    def setup_processor_with_process_instance(
        self,
        process_instance_model: ProcessInstanceModel,
        process_id_to_run: str | None = None,
        include_task_data_for_completed_tasks: bool = False,
        include_completed_subprocesses: bool = False,
    ) -> None:
        tld = current_app.config["THREAD_LOCAL_DATA"]
        tld.process_instance_id = process_instance_model.id

        # we want this to be the fully qualified path to the process model including all group subcomponents
        tld.process_model_identifier = f"{process_instance_model.process_model_identifier}"

        self.process_instance_model = process_instance_model
        bpmn_process_spec = None
        self.full_bpmn_process_dict: dict = {}

        # mappings of tasks and bpmn subprocesses to the model objects so we can avoid unnecessary queries in the TaskService.
        # only subprocesses should be necessary since the top-level process is on the process-instance and sqlalchemy
        # should help us cache it in memeory. it also does not have a guid which is why just avoid caching it in this system.
        self.task_model_mapping: dict[str, TaskModel] = {}
        self.bpmn_subprocess_mapping: dict[str, BpmnProcessModel] = {}
        self.bpmn_definition_to_task_definitions_mappings: dict = {}

        subprocesses: IdToBpmnProcessSpecMapping | None = None
        if not process_instance_model.spiffworkflow_fully_initialized():
            (
                bpmn_process_spec,
                subprocesses,
            ) = BpmnProcessService.get_process_model_and_subprocesses(
                process_instance_model.process_model_identifier, process_id_to_run=process_id_to_run
            )

        self.process_model_identifier = process_instance_model.process_model_identifier
        self.process_model_display_name = process_instance_model.process_model_display_name

        try:
            (
                self.bpmn_process_instance,
                self.full_bpmn_process_dict,
                self.bpmn_definition_to_task_definitions_mappings,
            ) = self.__class__.__get_bpmn_process_instance(
                process_instance_model,
                spec=bpmn_process_spec,
                subprocesses=subprocesses,
                include_task_data_for_completed_tasks=include_task_data_for_completed_tasks,
                include_completed_subprocesses=include_completed_subprocesses,
                task_model_mapping=self.task_model_mapping,
                bpmn_subprocess_mapping=self.bpmn_subprocess_mapping,
            )
            self.set_script_engine(self.bpmn_process_instance, self._script_engine)

        except MissingSpecError as ke:
            raise ApiError(
                error_code="unexpected_process_instance_structure",
                message=(
                    f"Failed to deserialize process_instance '{self.process_model_identifier}' due to a mis-placed or"
                    f" missing task '{str(ke)}'"
                ),
            ) from ke

    @classmethod
    def persist_bpmn_process_dict(
        cls,
        bpmn_process_dict: dict,
        bpmn_definition_to_task_definitions_mappings: dict,
        process_instance_model: ProcessInstanceModel,
        store_process_instance_events: bool = True,
        bpmn_process_instance: BpmnWorkflow | None = None,
    ) -> None:
        # NOTE: the first add_bpmn_process_definitions is to save the objects to the database and the second
        # is to load them so we can get the db id's.
        # We could potentially do this at save time by recreating the mappings var after getting the new id.
        process_instance_model.bpmn_process_definition = BpmnProcessService.add_bpmn_process_definitions(
            bpmn_process_dict,
            bpmn_definition_to_task_definitions_mappings=bpmn_definition_to_task_definitions_mappings,
        )
        BpmnProcessService.save_to_database(
            bpmn_definition_to_task_definitions_mappings,
            bpmn_process_definition_parent=process_instance_model.bpmn_process_definition,
        )
        bpmn_definition_to_task_definitions_mappings = {}
        process_instance_model.bpmn_process_definition = BpmnProcessService.add_bpmn_process_definitions(
            bpmn_process_dict,
            bpmn_definition_to_task_definitions_mappings=bpmn_definition_to_task_definitions_mappings,
        )

        if bpmn_process_instance is None:
            bpmn_process_instance = cls.initialize_bpmn_process_instance(bpmn_process_dict)

        task_model_mapping, bpmn_subprocess_mapping = cls.get_db_mappings_from_bpmn_process_dict(bpmn_process_dict)

        task_service = TaskService(
            process_instance=process_instance_model,
            serializer=BpmnProcessService.serializer,
            bpmn_definition_to_task_definitions_mappings=bpmn_definition_to_task_definitions_mappings,
            force_update_definitions=True,
            task_model_mapping=task_model_mapping,
            bpmn_subprocess_mapping=bpmn_subprocess_mapping,
        )

        for spiff_task in bpmn_process_instance.get_tasks():
            start_and_end_times: StartAndEndTimes | None = None
            if spiff_task.has_state(TaskState.COMPLETED | TaskState.ERROR):
                start_and_end_times = {
                    "start_in_seconds": spiff_task.last_state_change,
                    "end_in_seconds": spiff_task.last_state_change,
                }
            task_service.update_task_model_with_spiff_task(
                spiff_task, store_process_instance_events=store_process_instance_events, start_and_end_times=start_and_end_times
            )
        task_service.save_objects_to_database()
        db.session.commit()

    @classmethod
    def initialize_bpmn_process_instance(cls, bpmn_process_dict: dict) -> BpmnWorkflow:
        process_copy = copy.deepcopy(bpmn_process_dict)
        bpmn_process_instance = BpmnProcessService.serializer.from_dict(process_copy)
        bpmn_process_instance.script_engine = cls._default_script_engine
        return bpmn_process_instance

    @classmethod
    def get_db_mappings_from_bpmn_process_dict(
        cls, bpmn_process_dict: dict
    ) -> tuple[dict[str, TaskModel], dict[str, BpmnProcessModel]]:
        task_guids = set(bpmn_process_dict["tasks"].keys())
        bpmn_process_guids = set()
        for subproc_guid, subproc_dict in bpmn_process_dict["subprocesses"].items():
            new_set = set(subproc_dict["tasks"].keys())
            task_guids.union(new_set)
            bpmn_process_guids.add(subproc_guid)
        task_models = TaskModel.query.filter(TaskModel.guid.in_(task_guids)).all()  # type: ignore
        bpmn_process_models = BpmnProcessModel.query.filter(BpmnProcessModel.guid.in_(bpmn_process_guids)).all()  # type: ignore
        task_model_mapping = {t.guid: t for t in task_models}
        bpmn_subprocess_mapping = {b.guid: b for b in bpmn_process_models}
        return (task_model_mapping, bpmn_subprocess_mapping)

    @classmethod
    def get_bpmn_process_instance_from_process_model(cls, process_model_identifier: str) -> BpmnWorkflow:
        (bpmn_process_spec, subprocesses) = BpmnProcessService.get_process_model_and_subprocesses(
            process_model_identifier,
        )
        bpmn_process_instance = BpmnProcessService.get_bpmn_process_instance_from_workflow_spec(bpmn_process_spec, subprocesses)
        cls.set_script_engine(bpmn_process_instance)
        return bpmn_process_instance

    @staticmethod
    def set_script_engine(bpmn_process_instance: BpmnWorkflow, script_engine: PythonScriptEngine | None = None) -> None:
        script_engine_to_use = script_engine or ProcessInstanceProcessor._default_script_engine
        script_engine_to_use.environment.restore_state(bpmn_process_instance)
        bpmn_process_instance.script_engine = script_engine_to_use

    @classmethod
    def _get_bpmn_process_dict(
        cls,
        bpmn_process: BpmnProcessModel,
        task_model_mapping: dict[str, TaskModel],
        get_tasks: bool = False,
        include_task_data_for_completed_tasks: bool = False,
    ) -> dict:
        json_data = JsonDataModel.query.filter_by(hash=bpmn_process.json_data_hash).first()
        bpmn_process_dict = {"data": json_data.data, "tasks": {}}
        bpmn_process_dict.update(bpmn_process.properties_json)
        if get_tasks:
            tasks = TaskModel.query.filter_by(bpmn_process_id=bpmn_process.id).all()
            cls._get_tasks_dict(
                tasks,
                bpmn_process_dict,
                include_task_data_for_completed_tasks=include_task_data_for_completed_tasks,
                task_model_mapping=task_model_mapping,
            )
        return bpmn_process_dict

    @classmethod
    def _get_tasks_dict(
        cls,
        tasks: list[TaskModel],
        spiff_bpmn_process_dict: dict,
        task_model_mapping: dict[str, TaskModel],
        bpmn_subprocess_id_to_guid_mappings: dict | None = None,
        include_task_data_for_completed_tasks: bool = False,
    ) -> None:
        json_data_hashes = set()
        states_to_exclude_from_rehydration: list[str] = []
        if not include_task_data_for_completed_tasks:
            # load CANCELLED task data for Gateways since they are marked as CANCELLED
            # and we need the task data from their parents
            states_to_exclude_from_rehydration = ["COMPLETED", "ERROR"]

        task_list_by_hash = {t.guid: t for t in tasks}
        task_guids_to_add = set()
        for task in tasks:
            parent_guid = task.parent_guid()
            if task.state not in states_to_exclude_from_rehydration:
                json_data_hashes.add(task.json_data_hash)
                task_guids_to_add.add(task.guid)

                # load parent task data to avoid certain issues that can arise from parallel branches
                if (
                    parent_guid in task_list_by_hash
                    and task_list_by_hash[parent_guid].state in states_to_exclude_from_rehydration
                ):
                    json_data_hashes.add(task_list_by_hash[parent_guid].json_data_hash)
                    task_guids_to_add.add(parent_guid)
            elif (
                parent_guid in task_list_by_hash
                and "instance_map" in (task_list_by_hash[parent_guid].runtime_info or {})
                and task_list_by_hash[parent_guid] not in states_to_exclude_from_rehydration
            ):
                # make sure we add task data for multi-instance tasks as well
                json_data_hashes.add(task.json_data_hash)
                task_guids_to_add.add(task.guid)

        json_data_records = JsonDataModel.query.filter(JsonDataModel.hash.in_(json_data_hashes)).all()  # type: ignore
        json_data_mappings = {}
        for json_data_record in json_data_records:
            json_data_mappings[json_data_record.hash] = json_data_record.data
        for task in tasks:
            tasks_dict = spiff_bpmn_process_dict["tasks"]
            if bpmn_subprocess_id_to_guid_mappings:
                bpmn_subprocess_guid = bpmn_subprocess_id_to_guid_mappings[task.bpmn_process_id]
                tasks_dict = spiff_bpmn_process_dict["subprocesses"][bpmn_subprocess_guid]["tasks"]
            tasks_dict[task.guid] = task.properties_json
            task_data = {}
            if task.guid in task_guids_to_add:
                task_data = json_data_mappings[task.json_data_hash]
            tasks_dict[task.guid]["data"] = task_data
            task_model_mapping[task.guid] = task

    @classmethod
    def _get_full_bpmn_process_dict(
        cls,
        bpmn_definition_to_task_definitions_mappings: dict,
        bpmn_subprocess_mapping: dict[str, BpmnProcessModel],
        task_model_mapping: dict[str, TaskModel],
        spiff_serializer_version: str | None = None,
        bpmn_process_definition: BpmnProcessDefinitionModel | None = None,
        bpmn_process: BpmnProcessModel | None = None,
        bpmn_process_definition_id: int | None = None,
        include_task_data_for_completed_tasks: bool = False,
        include_completed_subprocesses: bool = False,
    ) -> dict:
        if bpmn_process_definition_id is None:
            return {}

        spiff_bpmn_process_dict: dict = {
            "serializer_version": spiff_serializer_version,
            "spec": {},
            "subprocess_specs": {},
            "subprocesses": {},
        }

        if bpmn_process_definition is not None:
            spiff_bpmn_process_dict["spec"] = BpmnProcessService.get_definition_dict_for_bpmn_process_definition(
                bpmn_process_definition,
                bpmn_definition_to_task_definitions_mappings,
            )
            BpmnProcessService.set_definition_dict_for_bpmn_subprocess_definitions(
                bpmn_process_definition,
                spiff_bpmn_process_dict,
                bpmn_definition_to_task_definitions_mappings,
            )

            if bpmn_process is not None:
                single_bpmn_process_dict = cls._get_bpmn_process_dict(
                    bpmn_process,
                    get_tasks=True,
                    include_task_data_for_completed_tasks=include_task_data_for_completed_tasks,
                    task_model_mapping=task_model_mapping,
                )
                spiff_bpmn_process_dict.update(single_bpmn_process_dict)

                bpmn_subprocesses_query = BpmnProcessModel.query.filter_by(top_level_process_id=bpmn_process.id)
                if not include_completed_subprocesses:
                    bpmn_subprocesses_query = bpmn_subprocesses_query.join(
                        TaskModel, TaskModel.guid == BpmnProcessModel.guid
                    ).filter(
                        TaskModel.state.not_in(["COMPLETED", "ERROR", "CANCELLED"])  # type: ignore
                    )
                bpmn_subprocesses = bpmn_subprocesses_query.all()
                bpmn_subprocess_id_to_guid_mappings = {}
                for bpmn_subprocess in bpmn_subprocesses:
                    subprocess_identifier = bpmn_subprocess.bpmn_process_definition.bpmn_identifier
                    if subprocess_identifier not in spiff_bpmn_process_dict["subprocess_specs"]:
                        current_app.logger.info(f"Deferring subprocess spec: '{subprocess_identifier}'")
                        continue
                    bpmn_subprocess_id_to_guid_mappings[bpmn_subprocess.id] = bpmn_subprocess.guid
                    single_bpmn_process_dict = cls._get_bpmn_process_dict(bpmn_subprocess, task_model_mapping=task_model_mapping)
                    spiff_bpmn_process_dict["subprocesses"][bpmn_subprocess.guid] = single_bpmn_process_dict
                    bpmn_subprocess_mapping[bpmn_subprocess.guid] = bpmn_subprocess

                tasks = TaskModel.query.filter(
                    TaskModel.bpmn_process_id.in_(bpmn_subprocess_id_to_guid_mappings.keys())  # type: ignore
                ).all()
                cls._get_tasks_dict(
                    tasks,
                    spiff_bpmn_process_dict,
                    bpmn_subprocess_id_to_guid_mappings=bpmn_subprocess_id_to_guid_mappings,
                    include_task_data_for_completed_tasks=include_task_data_for_completed_tasks,
                    task_model_mapping=task_model_mapping,
                )

        return spiff_bpmn_process_dict

    def current_user(self) -> Any:
        current_user = None
        if UserService.has_user():
            current_user = UserService.current_user()

        # fall back to initiator if g.user is not set
        # this is for background processes when there will not be a user
        #   coming in from the api
        elif self.process_instance_model.process_initiator_id:
            current_user = self.process_instance_model.process_initiator

        return current_user

    @staticmethod
    def __get_bpmn_process_instance(
        process_instance_model: ProcessInstanceModel,
        task_model_mapping: dict[str, TaskModel],
        bpmn_subprocess_mapping: dict[str, BpmnProcessModel],
        spec: BpmnProcessSpec | None = None,
        subprocesses: IdToBpmnProcessSpecMapping | None = None,
        include_task_data_for_completed_tasks: bool = False,
        include_completed_subprocesses: bool = False,
    ) -> tuple[BpmnWorkflow, dict, dict]:
        full_bpmn_process_dict = {}
        bpmn_definition_to_task_definitions_mappings: dict = {}
        if process_instance_model.spiffworkflow_fully_initialized():
            # turn off logging to avoid duplicated spiff logs
            spiff_logger = logging.getLogger("spiff")
            original_spiff_logger_log_level = spiff_logger.level
            spiff_logger.setLevel(logging.WARNING)

            try:
                full_bpmn_process_dict = ProcessInstanceProcessor._get_full_bpmn_process_dict(
                    bpmn_definition_to_task_definitions_mappings=bpmn_definition_to_task_definitions_mappings,
                    include_completed_subprocesses=include_completed_subprocesses,
                    include_task_data_for_completed_tasks=include_task_data_for_completed_tasks,
                    task_model_mapping=task_model_mapping,
                    bpmn_subprocess_mapping=bpmn_subprocess_mapping,
                    spiff_serializer_version=process_instance_model.spiff_serializer_version,
                    bpmn_process_definition=process_instance_model.bpmn_process_definition,
                    bpmn_process=process_instance_model.bpmn_process,
                    bpmn_process_definition_id=process_instance_model.bpmn_process_definition_id,
                )
                # FIXME: the from_dict entrypoint in spiff will one day do this copy instead
                process_copy = copy.deepcopy(full_bpmn_process_dict)
                bpmn_process_instance = BpmnProcessService.serializer.from_dict(process_copy)
                bpmn_process_instance.get_tasks()
            except Exception as err:
                raise err
            finally:
                spiff_logger.setLevel(original_spiff_logger_log_level)
        else:
            bpmn_process_instance = BpmnProcessService.get_bpmn_process_instance_from_workflow_spec(spec, subprocesses)

        return (
            bpmn_process_instance,
            full_bpmn_process_dict,
            bpmn_definition_to_task_definitions_mappings,
        )

    def add_data_to_bpmn_process_instance(self, data: dict) -> None:
        # if we do not use a deep merge, then the data does not end up on the object for some reason
        self.bpmn_process_instance.data = DeepMerge.merge(self.bpmn_process_instance.data, data)

    def raise_if_no_potential_owners(self, potential_owners: list[PotentialOwner], message: str) -> None:
        if not potential_owners:
            raise NoPotentialOwnersForTaskError(message)

    def get_potential_owners_from_task(self, task: SpiffTask) -> PotentialOwnerIdList:
        task_spec = task.task_spec
        task_lane = "process_initiator"

        if current_app.config.get("SPIFFWORKFLOW_BACKEND_USE_LANES_FOR_TASK_ASSIGNMENT") is not False:
            if task_spec.lane is not None and task_spec.lane != "":
                task_lane = task_spec.lane

        potential_owners: list[PotentialOwner] = []
        lane_assignment_id = None

        if "allowGuest" in task.task_spec.extensions and task.task_spec.extensions["allowGuest"] == "true":
            guest_user = UserService.find_or_create_guest_user()
            potential_owners = [{"added_by": HumanTaskUserAddedBy.guest.value, "user_id": guest_user.id}]
        elif re.match(r"(process.?)initiator", task_lane, re.IGNORECASE):
            potential_owners = [
                {
                    "added_by": HumanTaskUserAddedBy.process_initiator.value,
                    "user_id": self.process_instance_model.process_initiator_id,
                }
            ]
        else:
            # Automatically create the group if it doesn't exist (includes principal creation)
            group_model = UserService.find_or_create_group(task_lane)
            lane_assignment_id = group_model.id
            if "lane_owners" in task.data and task_lane in task.data["lane_owners"]:
                for username_or_email in task.data["lane_owners"][task_lane]:
                    lane_owner_user = UserModel.query.filter(
                        or_(UserModel.username == username_or_email, UserModel.email == username_or_email)
                    ).first()
                    if lane_owner_user is not None:
                        potential_owners.append(
                            {"added_by": HumanTaskUserAddedBy.lane_owner.value, "user_id": lane_owner_user.id}
                        )
                self.raise_if_no_potential_owners(
                    potential_owners,
                    (
                        "No users found in task data lane owner list for lane:"
                        f" {task_lane}. The user list used:"
                        f" {task.data['lane_owners'][task_lane]}"
                    ),
                )
            else:
                potential_owners = [
                    {"added_by": HumanTaskUserAddedBy.lane_assignment.value, "user_id": i.user_id}
                    for i in group_model.user_group_assignments
                ]

        return {
            "potential_owners": potential_owners,
            "lane_assignment_id": lane_assignment_id,
        }

    def extract_metadata(self) -> dict:
        return ProcessModelService.extract_metadata(
            self.process_instance_model.process_model_identifier,
            self.get_current_data(),
        )

    def store_metadata(self, metadata: dict) -> None:
        for key, data_for_key in metadata.items():
            if data_for_key is not None:
                pim = ProcessInstanceMetadataModel.query.filter_by(
                    process_instance_id=self.process_instance_model.id,
                    key=key,
                ).first()
                if pim is None:
                    pim = ProcessInstanceMetadataModel(
                        process_instance_id=self.process_instance_model.id,
                        key=key,
                    )
                pim.value = self.__class__.truncate_string(str(data_for_key), 255)
                db.session.add(pim)

    def update_summary(self) -> None:
        current_data = self.get_current_data()
        if "spiff_process_instance_summary" in current_data:
            summary = current_data["spiff_process_instance_summary"]
            self.process_instance_model.summary = self.__class__.truncate_string(summary, 255)

    @classmethod
    def truncate_string(cls, input_string: str | None, max_length: int) -> str | None:
        if input_string is None:
            return None
        return input_string[:max_length]

    def save(self) -> None:
        """Saves the current state of this processor to the database."""
        self.process_instance_model.spiff_serializer_version = SPIFFWORKFLOW_BACKEND_SERIALIZER_VERSION
        self.process_instance_model.status = self.get_status().value
        current_app.logger.debug(
            f"the_status: {self.process_instance_model.status} for instance {self.process_instance_model.id}"
        )
        bpmn_process_definition_dict = {
            "single_process_hash": self.process_instance_model.bpmn_process_definition.single_process_hash,
            "full_process_model_hash": self.process_instance_model.bpmn_process_definition.full_process_model_hash,
            "bpmn_identifier": self.process_instance_model.bpmn_process_definition.bpmn_identifier,
            "bpmn_name": self.process_instance_model.bpmn_process_definition.bpmn_name,
            "properties_json": self.process_instance_model.bpmn_process_definition.properties_json,
        }
        BpmnProcessDefinitionModel.insert_or_update_record(bpmn_process_definition_dict)

        if self.process_instance_model.start_in_seconds is None:
            self.process_instance_model.start_in_seconds = round(time.time())

        metadata = self.extract_metadata()
        if self.process_instance_model.end_in_seconds is None:
            if self.bpmn_process_instance.is_completed():
                self.process_instance_model.end_in_seconds = round(time.time())
                if self._workflow_completed_handler is not None:
                    self._workflow_completed_handler(self.process_instance_model)
                log_extras = {
                    "milestone": "Completed",
                    "process_model_identifier": self.process_instance_model.process_model_identifier,
                    "process_instance_id": self.process_instance_model.id,
                    "metadata": metadata,
                }
                LoggingService.log_event(ProcessInstanceEventType.process_instance_completed.value, log_extras)
                queue_event_notifier_if_appropriate(self.process_instance_model, "process_instance_complete")

        db.session.add(self.process_instance_model)

        new_human_tasks = []
        initial_human_tasks = HumanTaskModel.query.filter_by(
            process_instance_id=self.process_instance_model.id, completed=False
        ).all()
        ready_or_waiting_tasks = self.get_all_ready_or_waiting_tasks()

        self.store_metadata(metadata)
        self.update_summary()

        for ready_or_waiting_task in ready_or_waiting_tasks:
            # filter out non-usertasks
            task_spec = ready_or_waiting_task.task_spec
            if task_spec.manual:
                potential_owner_hash = self.get_potential_owners_from_task(ready_or_waiting_task)
                extensions = task_spec.extensions

                # in the xml, it's the id attribute. this identifies the process where the activity lives.
                # if it's in a subprocess, it's the inner process.
                bpmn_process_identifier = ready_or_waiting_task.workflow.spec.name

                form_file_name = None
                ui_form_file_name = None
                json_metadata = {}
                if "taskMetadataValues" in extensions:
                    task_metadata_values = extensions["taskMetadataValues"]
                    # Process each taskMetadataValue using the script engine
                    for key, value in task_metadata_values.items():
                        try:
                            json_metadata[key] = self._script_engine.evaluate(ready_or_waiting_task, value)
                        except Exception as e:
                            current_app.logger.warning(
                                f"Failed to evaluate taskMetadataValue {key} for task {ready_or_waiting_task.task_spec.name}: {e}"
                            )
                            msg = f"Failed to evaluate taskMetadataValue {key}: {e}"
                            json_metadata[f"{key}_error"] = msg

                if "properties" in extensions:
                    properties = extensions["properties"]
                    if "formJsonSchemaFilename" in properties:
                        form_file_name = properties["formJsonSchemaFilename"]
                    if "formUiSchemaFilename" in properties:
                        ui_form_file_name = properties["formUiSchemaFilename"]

                human_task = None
                for at in initial_human_tasks:
                    if at.task_id == str(ready_or_waiting_task.id):
                        human_task = at
                        initial_human_tasks.remove(at)

                if human_task is None:
                    task_guid = str(ready_or_waiting_task.id)
                    task_model = TaskModel.query.filter_by(guid=task_guid).first()
                    if task_model is None:
                        raise TaskNotFoundError(f"Could not find task for human task with guid: {task_guid}")

                    human_task = HumanTaskModel(
                        process_instance_id=self.process_instance_model.id,
                        process_model_display_name=self.process_instance_model.process_model_display_name,
                        bpmn_process_identifier=bpmn_process_identifier,
                        form_file_name=form_file_name,
                        ui_form_file_name=ui_form_file_name,
                        task_guid=task_model.guid,
                        task_id=task_guid,
                        task_name=ready_or_waiting_task.task_spec.bpmn_id,
                        task_title=self.__class__.truncate_string(ready_or_waiting_task.task_spec.bpmn_name, 255),
                        task_type=ready_or_waiting_task.task_spec.__class__.__name__,
                        task_status=TaskState.get_name(ready_or_waiting_task.state),
                        lane_assignment_id=potential_owner_hash["lane_assignment_id"],
                        lane_name=self.__class__.truncate_string(ready_or_waiting_task.task_spec.lane, 255),
                        json_metadata=json_metadata,
                    )
                    db.session.add(human_task)
                    new_human_tasks.append(human_task)

                    for potential_owner in potential_owner_hash["potential_owners"]:
                        human_task_user = HumanTaskUserModel(
                            user_id=potential_owner["user_id"], added_by=potential_owner["added_by"], human_task=human_task
                        )
                        db.session.add(human_task_user)

        if len(new_human_tasks) > 0:
            queue_event_notifier_if_appropriate(self.process_instance_model, "human_task_available")

        if len(initial_human_tasks) > 0:
            for at in initial_human_tasks:
                at.completed = True
                db.session.add(at)
        db.session.commit()

    def serialize_task_spec(self, task_spec: SpiffTask) -> dict:
        """Get a serialized version of a task spec."""
        # The task spec is NOT actually a SpiffTask, it is the task spec attached to a SpiffTask
        # Not sure why mypy accepts this but whatever.
        result: dict = BpmnProcessService.serializer.to_dict(task_spec)
        return result

    def send_bpmn_event(self, event_data: dict[str, Any]) -> None:
        """Send an event to the workflow."""
        payload = event_data.pop("payload", None)
        event_definition = BpmnProcessService.serializer.from_dict(event_data)
        bpmn_event = BpmnEvent(
            event_definition=event_definition,
            payload=payload,
        )
        try:
            self.bpmn_process_instance.send_event(bpmn_event)
        except Exception as e:
            current_app.logger.warning(e)

        # TODO: do_engine_steps without a lock
        self.do_engine_steps(save=True)

    def manual_complete_task(self, task_id: str, execute: bool, user: UserModel) -> None:
        """Mark the task complete optionally executing it."""
        spiff_task = self.bpmn_process_instance.get_task_from_id(UUID(task_id))
        event_type = ProcessInstanceEventType.task_skipped.value
        if execute:
            event_type = ProcessInstanceEventType.task_executed_manually.value

        start_time = time.time()

        # manual actually means any human task
        if spiff_task.task_spec.manual:
            # Executing or not executing a human task results in the same state.
            current_app.logger.info(
                f"Manually skipping Human Task {spiff_task.task_spec.name} of process instance {self.process_instance_model.id}"
            )
            human_task = HumanTaskModel.query.filter_by(task_id=task_id).first()
            self.complete_task(spiff_task, user=user, human_task=human_task)
        elif execute:
            current_app.logger.info(
                f"Manually executing Task {spiff_task.task_spec.name} of process instance {self.process_instance_model.id}"
            )
            self.do_engine_steps(save=True, execution_strategy_name="run_current_ready_tasks", ignore_cannot_be_run_error=True)
        else:
            current_app.logger.info(f"Skipped task {spiff_task.task_spec.name}", extra=spiff_task.collect_log_extras())
            task_model_delegate = TaskModelSavingDelegate(
                serializer=BpmnProcessService.serializer,
                process_instance=self.process_instance_model,
                bpmn_definition_to_task_definitions_mappings=self.bpmn_definition_to_task_definitions_mappings,
            )
            execution_strategy = SkipOneExecutionStrategy(task_model_delegate, {"spiff_task": spiff_task})
            self.do_engine_steps(save=True, execution_strategy=execution_strategy, ignore_cannot_be_run_error=True)

        spiff_tasks = self.bpmn_process_instance.get_tasks()
        task_service = TaskService(
            process_instance=self.process_instance_model,
            serializer=BpmnProcessService.serializer,
            bpmn_definition_to_task_definitions_mappings=self.bpmn_definition_to_task_definitions_mappings,
            bpmn_subprocess_mapping=self.bpmn_subprocess_mapping,
            task_model_mapping=self.task_model_mapping,
        )
        task_service.update_all_tasks_from_spiff_tasks(spiff_tasks, [], start_time)
        ProcessInstanceTmpService.add_event_to_process_instance(self.process_instance_model, event_type, task_guid=task_id)

        self.save()
        # Saving the workflow seems to reset the status
        self.suspend()

    @classmethod
    def reset_process(cls, process_instance: ProcessInstanceModel, to_task_guid: str) -> None:
        """Reset a process to an earlier state."""
        start_time = time.time()

        # Log the event that we are moving back to a previous task.
        ProcessInstanceTmpService.add_event_to_process_instance(
            process_instance, ProcessInstanceEventType.process_instance_rewound_to_task.value, task_guid=to_task_guid
        )
        processor = ProcessInstanceProcessor(
            process_instance, include_task_data_for_completed_tasks=True, include_completed_subprocesses=True
        )
        deleted_tasks = processor.bpmn_process_instance.reset_from_task_id(UUID(to_task_guid))
        spiff_tasks = processor.bpmn_process_instance.get_tasks()

        for dt in deleted_tasks:
            if str(dt.id) in processor.task_model_mapping:
                del processor.task_model_mapping[str(dt.id)]
            if str(dt.id) in processor.bpmn_subprocess_mapping:
                del processor.bpmn_subprocess_mapping[str(dt.id)]

        task_service = TaskService(
            process_instance=processor.process_instance_model,
            serializer=BpmnProcessService.serializer,
            bpmn_definition_to_task_definitions_mappings=processor.bpmn_definition_to_task_definitions_mappings,
            task_model_mapping=processor.task_model_mapping,
            bpmn_subprocess_mapping=processor.bpmn_subprocess_mapping,
        )
        task_service.update_all_tasks_from_spiff_tasks(spiff_tasks, deleted_tasks, start_time, to_task_guid=to_task_guid)

        # Save the process
        processor.save()
        processor.suspend()

    @classmethod
    def update_guids_on_tasks(cls, bpmn_process_instance_dict: dict) -> None:
        # old -> new
        guid_map = {}

        def get_guid_map(proc_dict: dict) -> None:
            for guid in proc_dict["tasks"].keys():
                guid_map[guid] = str(uuid4())

        def update_guids(proc_dict: dict) -> None:
            new_tasks = {}
            for task_guid, task_dict in proc_dict["tasks"].items():
                new_guid = guid_map[task_guid]
                new_tasks[new_guid] = task_dict
                if task_dict["parent"] is not None:
                    new_tasks[new_guid]["parent"] = guid_map[task_dict["parent"]]
                new_children_guids = [guid_map[cg] for cg in task_dict["children"]]
                new_tasks[new_guid]["children"] = new_children_guids
                new_tasks[new_guid]["id"] = guid_map[task_dict["id"]]
            proc_dict["tasks"] = new_tasks
            proc_dict["root"] = guid_map[proc_dict["root"]]
            proc_dict["last_task"] = guid_map[proc_dict["last_task"]]

        get_guid_map(bpmn_process_instance_dict)
        for subproc_dict in bpmn_process_instance_dict["subprocesses"].values():
            get_guid_map(subproc_dict)

        update_guids(bpmn_process_instance_dict)
        new_subprocesses = {}
        for subproc_guid, subproc_dict in bpmn_process_instance_dict["subprocesses"].items():
            new_guid = guid_map[subproc_guid]
            new_subprocesses[new_guid] = subproc_dict
            new_subprocesses[new_guid]["parent_task_id"] = guid_map[subproc_dict["parent_task_id"]]
            update_guids(new_subprocesses[new_guid])
        bpmn_process_instance_dict["subprocesses"] = new_subprocesses

    @staticmethod
    def status_of(bpmn_process_instance: BpmnWorkflow) -> ProcessInstanceStatus:
        if bpmn_process_instance.is_completed():
            return ProcessInstanceStatus.complete
        user_tasks = bpmn_process_instance.get_tasks(state=TaskState.READY, manual=True)
        ready_tasks = bpmn_process_instance.get_tasks(state=TaskState.READY)

        # workflow.waiting_events (includes timers, and timers have a when firing property)

        # if the process instance has status "waiting" it will get picked up
        # by background processing. when that happens it can potentially overwrite
        # human tasks which is bad because we cache them with the previous id's.
        # waiting_tasks = bpmn_process_instance.get_tasks(state=TaskState.WAITING)
        # waiting_tasks = bpmn_process_instance.get_waiting()
        # if len(waiting_tasks) > 0:
        #     return ProcessInstanceStatus.waiting
        if len(user_tasks) > 0:
            return ProcessInstanceStatus.user_input_required
        elif len(ready_tasks) > 0:
            return ProcessInstanceStatus.running
        else:
            return ProcessInstanceStatus.waiting

    def get_status(self) -> ProcessInstanceStatus:
        the_status = self.status_of(self.bpmn_process_instance)
        # current_app.logger.debug(f"the_status: {the_status} for instance {self.process_instance_model.id}")
        return the_status

    def refresh_waiting_tasks(self) -> None:
        self.bpmn_process_instance.refresh_waiting_tasks()

    def do_engine_steps(
        self,
        exit_at: None = None,
        save: bool = False,
        execution_strategy_name: str | None = None,
        execution_strategy: ExecutionStrategy | None = None,
        should_schedule_waiting_timer_events: bool = True,
        ignore_cannot_be_run_error: bool = False,
        needs_dequeue: bool = True,
    ) -> TaskRunnability:
        if not ignore_cannot_be_run_error and not self.process_instance_model.allowed_to_run():
            raise ProcessInstanceCannotBeRunError(
                f"Process instance '{self.process_instance_model.id}' has status "
                f"'{self.process_instance_model.status}' and therefore cannot run."
            )
        if self.process_instance_model.persistence_level != "none":
            with ProcessInstanceQueueService.dequeued(self.process_instance_model, needs_dequeue=needs_dequeue):
                # TODO: ideally we just lock in the execution service, but not sure
                # about add_bpmn_process_definitions and if that needs to happen in
                # the same lock like it does on main
                return self._do_engine_steps(
                    exit_at,
                    save,
                    execution_strategy_name,
                    execution_strategy,
                    should_schedule_waiting_timer_events=should_schedule_waiting_timer_events,
                    needs_dequeue=needs_dequeue,
                )
        else:
            return self._do_engine_steps(
                exit_at,
                save=False,
                execution_strategy_name=execution_strategy_name,
                execution_strategy=execution_strategy,
                should_schedule_waiting_timer_events=should_schedule_waiting_timer_events,
            )

    def _do_engine_steps(
        self,
        exit_at: None = None,
        save: bool = False,
        execution_strategy_name: str | None = None,
        execution_strategy: ExecutionStrategy | None = None,
        should_schedule_waiting_timer_events: bool = True,
        needs_dequeue: bool = True,
    ) -> TaskRunnability:
        # Debug logs for engine steps execution
        process_id = self.process_instance_model.id
        current_status = self.process_instance_model.status
        ready_tasks = [t.task_spec.name for t in self.bpmn_process_instance.get_tasks(state=TaskState.READY)]
        waiting_tasks = [t.task_spec.name for t in self.get_all_waiting_tasks()]

        current_app.logger.debug(f"ENGINE STEPS - START: Process {process_id}, Status: {current_status}")
        current_app.logger.debug(f"ENGINE STEPS - Ready tasks: {ready_tasks}")
        current_app.logger.debug(f"ENGINE STEPS - Waiting tasks: {waiting_tasks}")

        self.raise_on_high_process_instance_count()

        if self.process_instance_model.bpmn_process is None:
            self.process_instance_model.bpmn_process_definition = BpmnProcessService.add_bpmn_process_definitions(  # type: ignore
                self.serialize(),
                bpmn_definition_to_task_definitions_mappings=self.bpmn_definition_to_task_definitions_mappings,
            )

        task_model_delegate = TaskModelSavingDelegate(
            serializer=BpmnProcessService.serializer,
            process_instance=self.process_instance_model,
            bpmn_definition_to_task_definitions_mappings=self.bpmn_definition_to_task_definitions_mappings,
            bpmn_subprocess_mapping=self.bpmn_subprocess_mapping,
            task_model_mapping=self.task_model_mapping,
        )

        if execution_strategy is None:
            if execution_strategy_name is None:
                execution_strategy_name = current_app.config["SPIFFWORKFLOW_BACKEND_ENGINE_STEP_DEFAULT_STRATEGY_WEB"]
            if execution_strategy_name is None:
                raise ExecutionStrategyNotConfiguredError(
                    "SPIFFWORKFLOW_BACKEND_ENGINE_STEP_DEFAULT_STRATEGY_WEB has not been set"
                )
            execution_strategy = execution_strategy_named(execution_strategy_name, task_model_delegate)

        execution_service = WorkflowExecutionService(
            self.bpmn_process_instance,
            self.process_instance_model,
            execution_strategy,
            self._script_engine.environment.finalize_result,
            self.save,
        )
        task_runnability = execution_service.run_and_save(
            exit_at,
            save,
            should_schedule_waiting_timer_events=should_schedule_waiting_timer_events,
            # profile=True,
            needs_dequeue=needs_dequeue,
        )
        self.task_model_mapping, self.bpmn_subprocess_mapping = task_model_delegate.get_guid_to_db_object_mappings()
        self.check_all_tasks()

        # Debug logs for engine steps completion
        new_status = self.get_status().value
        after_ready_tasks = [t.task_spec.name for t in self.bpmn_process_instance.get_tasks(state=TaskState.READY)]
        after_waiting_tasks = [t.task_spec.name for t in self.get_all_waiting_tasks()]

        current_app.logger.debug(f"ENGINE STEPS - FINISH: Process {process_id}, New Status: {new_status}")
        current_app.logger.debug(f"ENGINE STEPS - New Ready tasks: {after_ready_tasks}")
        current_app.logger.debug(f"ENGINE STEPS - New Waiting tasks: {after_waiting_tasks}")
        current_app.logger.debug(f"ENGINE STEPS - Task Runnability: {task_runnability}")

        return task_runnability

    def raise_on_high_process_instance_count(self) -> None:
        all_tasks = self.bpmn_process_instance.get_tasks(state=TaskState.ANY_MASK)
        if len(all_tasks) > MAX_PROCESS_INSTANCE_TASK_COUNT:
            msg = (
                f"Number of tasks generated for process instance exceeds safe count - {MAX_PROCESS_INSTANCE_TASK_COUNT}. "
                "This can usually happen if using numerous parallel gateway pairs. "
                "Try embedding each pair in a subprocess to reduce the number of tasks."
            )
            raise ProcessInstanceTaskCountExceededError(msg)

    @classmethod
    def get_tasks_with_data(cls, bpmn_process_instance: BpmnWorkflow) -> list[SpiffTask]:
        return [task for task in bpmn_process_instance.get_tasks(state=TaskState.FINISHED_MASK) if len(task.data) > 0]

    @classmethod
    def get_task_data_size(cls, bpmn_process_instance: BpmnWorkflow) -> int:
        tasks_with_data = cls.get_tasks_with_data(bpmn_process_instance)
        all_task_data = [task.data for task in tasks_with_data]

        try:
            return len(json.dumps(all_task_data))
        except Exception:
            return 0

    @classmethod
    def get_python_env_size(cls, bpmn_process_instance: BpmnWorkflow) -> int:
        user_defined_state = bpmn_process_instance.script_engine.environment.user_defined_state()

        try:
            return len(json.dumps(user_defined_state))
        except Exception:
            return 0

    def check_task_data_size(self) -> None:
        task_data_len = self.get_task_data_size(self.bpmn_process_instance)

        # Not sure what the number here should be but this now matches the mysql
        # max_allowed_packet variable on dev - 1073741824
        task_data_limit = 1024**3

        if task_data_len > task_data_limit:
            raise (
                ApiError(
                    error_code="task_data_size_exceeded",
                    message=f"Maximum task data size of {task_data_limit} exceeded.",
                )
            )

    def serialize(self, serialize_script_engine_state: bool = True) -> dict:
        self.check_task_data_size()

        if serialize_script_engine_state:
            self._script_engine.environment.preserve_state(self.bpmn_process_instance)

        result = BpmnProcessService.serializer.to_dict(self.bpmn_process_instance)

        if not serialize_script_engine_state and "data" in result:
            self._script_engine.environment.pop_state(result["data"])

        return result  # type: ignore

    def next_user_tasks(self) -> list[SpiffTask]:
        return self.bpmn_process_instance.get_tasks(state=TaskState.READY, manual=True)  # type: ignore

    def next_task(self) -> SpiffTask:
        """Returns the next task that should be completed even if there are parallel tasks and multiple options are available.

        If the process_instance is complete it will return the final end task.
        If the process_instance is in an error state it will return the task that is erroring.
        """
        # If the whole blessed mess is done, return the end_event task in the tree
        # This was failing in the case of a call activity where we have an intermediate EndEvent
        # what we really want is the LAST EndEvent

        endtasks = []
        if self.bpmn_process_instance.is_completed():
            for spiff_task in TaskIterator(self.bpmn_process_instance.task_tree, TaskState.ANY_MASK):
                # Assure that we find the end event for this process_instance, and not for any sub-process_instances.
                if TaskService.is_main_process_end_event(spiff_task):
                    endtasks.append(spiff_task)
            if len(endtasks) > 0:
                return endtasks[-1]

        # If there are ready tasks to complete, return the next ready task, but return the one
        # in the active parallel path if possible.  In some cases the active parallel path may itself be
        # a parallel gateway with multiple tasks, so prefer ones that share a parent.

        # Get a list of all ready tasks
        ready_tasks = self.bpmn_process_instance.get_tasks(state=TaskState.READY)

        if len(ready_tasks) == 0:
            # If no ready tasks exist, check for a waiting task.
            waiting_tasks = self.bpmn_process_instance.get_tasks(state=TaskState.WAITING)
            if len(waiting_tasks) > 0:
                return waiting_tasks[0]

            # If there are no ready tasks, and not waiting tasks, return the latest error.
            error_task = None
            for task in TaskIterator(self.bpmn_process_instance.task_tree, TaskState.ERROR):
                error_task = task
            return error_task

        # Get a list of all completed user tasks (Non engine tasks)
        completed_user_tasks = self.completed_user_tasks()

        # If there are no completed user tasks, return the first ready task
        if len(completed_user_tasks) == 0:
            return ready_tasks[0]

        # Take the last completed task, find a child of it, and return that task
        last_user_task = completed_user_tasks[0]
        if len(ready_tasks) > 0:
            for task in ready_tasks:
                if task.is_descendant_of(last_user_task):
                    return task
            for task in ready_tasks:
                if self.bpmn_process_instance.last_task and task.parent == last_user_task.parent:
                    return task

            return ready_tasks[0]

        # If there are no ready tasks, but the thing isn't complete yet, find the first non-complete task
        # and return that
        next_task_to_return = None
        for task in TaskIterator(self.bpmn_process_instance.task_tree, TaskState.NOT_FINISHED_MASK):
            next_task_to_return = task
        return next_task_to_return

    def completed_user_tasks(self) -> list[SpiffTask]:
        user_tasks = self.bpmn_process_instance.get_tasks(state=TaskState.COMPLETED)
        user_tasks.reverse()
        user_tasks = list(
            filter(
                lambda task: task.task_spec.manual,
                user_tasks,
            )
        )
        return user_tasks

    def get_task_dict_from_spiff_task(self, spiff_task: SpiffTask) -> dict[str, Any]:
        default_registry = DefaultRegistry()
        task_data = default_registry.convert(spiff_task.data)
        python_env = default_registry.convert(self._script_engine.environment.last_result())
        task_json: dict[str, Any] = {
            "task_data": task_data,
            "python_env": python_env,
        }
        return task_json

    def complete_task(self, spiff_task: SpiffTask, user: UserModel, human_task: HumanTaskModel | None = None) -> None:
        task_model = TaskModel.query.filter_by(guid=str(spiff_task.id)).first()
        if task_model is None:
            raise TaskNotFoundError(f"Cannot find a task with guid {spiff_task.id}")

        if human_task and str(spiff_task.id) != human_task.task_guid:
            raise TaskMismatchError(
                f"Given spiff task ({spiff_task.task_spec.bpmn_id} - {spiff_task.id}) and human task ({human_task.task_name} -"
                f" {human_task.task_guid}) must match"
            )

        run_started_at = time.time()
        task_model.start_in_seconds = run_started_at
        task_exception = None
        task_event = ProcessInstanceEventType.task_completed.value
        try:
            if isinstance(spiff_task.task_spec, ServiceTask) and spiff_task.state == TaskState.STARTED:
                # We are manually completing a service task, we should not execute it. Just mark it as complete.
                spiff_task.complete()
            else:
                self.bpmn_process_instance.run_task_from_id(spiff_task.id)
        except Exception as ex:
            task_exception = ex
            task_event = ProcessInstanceEventType.task_failed.value

        task_model.end_in_seconds = time.time()

        if human_task:
            human_task.completed_by_user_id = user.id
            human_task.completed = True
            human_task.task_status = TaskState.get_name(spiff_task.state)
            db.session.add(human_task)

        task_service = TaskService(
            process_instance=self.process_instance_model,
            serializer=BpmnProcessService.serializer,
            bpmn_definition_to_task_definitions_mappings=self.bpmn_definition_to_task_definitions_mappings,
            run_started_at=run_started_at,
            bpmn_subprocess_mapping=self.bpmn_subprocess_mapping,
            task_model_mapping=self.task_model_mapping,
        )
        task_service.update_task_model(task_model, spiff_task)
        JsonDataModel.insert_or_update_json_data_records(task_service.json_data_dicts)

        ProcessInstanceTmpService.add_event_to_process_instance(
            self.process_instance_model,
            task_event,
            task_guid=task_model.guid,
            user=user,
            exception=task_exception,
            log_event=False,
        )

        log_extras = {
            "task_id": str(spiff_task.id),
            "task_spec": spiff_task.task_spec.name,
            "bpmn_name": spiff_task.task_spec.bpmn_name,
            "process_model_identifier": self.process_instance_model.process_model_identifier,
            "process_instance_id": self.process_instance_model.id,
            "metadata": self.extract_metadata(),
        }
        LoggingService.log_event(task_event, log_extras)

        # children of a multi-instance task has the attribute "triggered" set to True
        # so use that to determine if a spiff_task is apart of a multi-instance task
        # and therefore we need to process its parent since the current task will not
        # know what is actually going on.
        # Basically "triggered" means "this task is not part of the task spec outputs"
        if spiff_task.triggered is True:
            spiff_task_to_process = spiff_task.parent
            task_service.update_task_model_with_spiff_task(spiff_task_to_process)

        tasks_to_update = self.bpmn_process_instance.get_tasks(updated_ts=run_started_at)
        for spiff_task_to_update in tasks_to_update:
            if spiff_task_to_update.id != spiff_task.id:
                task_service.update_task_model_with_spiff_task(spiff_task_to_update)
        self.task_model_mapping, self.bpmn_subprocess_mapping = task_service.get_guid_to_db_object_mappings()

        task_service.save_objects_to_database()

        # this is the thing that actually commits the db transaction (on behalf of the other updates above as well)
        self.save()

        if task_exception is not None:
            raise task_exception

    def get_data(self) -> dict[str, Any]:
        return self.bpmn_process_instance.data  # type: ignore

    def get_current_data(self) -> dict[str, Any]:
        """Get the current data for the process.

        Return either the most recent task data or--if the process instance is complete--
        the process data.
        """
        if self.process_instance_model.status == ProcessInstanceStatus.complete.value:
            return self.get_data()

        most_recent_task = None
        for task in self.get_all_ready_or_waiting_tasks():
            if most_recent_task is None:
                most_recent_task = task
            elif most_recent_task.last_state_change < task.last_state_change:
                most_recent_task = task

        if most_recent_task:
            return most_recent_task.data  # type: ignore

        return {}

    def get_process_instance_id(self) -> int:
        return self.process_instance_model.id

    def get_ready_user_tasks(self) -> list[SpiffTask]:
        return self.bpmn_process_instance.get_tasks(state=TaskState.READY, manual=True)  # type: ignore

    def get_current_user_tasks(self) -> list[SpiffTask]:
        """Return a list of all user tasks that are READY or COMPLETE and are parallel to the READY Task."""
        ready_tasks = self.bpmn_process_instance.get_tasks(state=TaskState.READY, manual=True)
        additional_tasks = []
        if len(ready_tasks) > 0:
            for child in ready_tasks[0].parent.children:
                if child.state == TaskState.COMPLETED:
                    additional_tasks.append(child)
        return ready_tasks + additional_tasks  # type: ignore

    def get_all_user_tasks(self) -> list[SpiffTask]:
        all_tasks = self.bpmn_process_instance.get_tasks(state=TaskState.ANY_MASK)
        return [t for t in all_tasks if t.task_spec.manual]

    def get_all_completed_tasks(self) -> list[SpiffTask]:
        return_tasks: list[SpiffTask] = self.bpmn_process_instance.get_tasks(state=TaskState.COMPLETED | TaskState.CANCELLED)
        return return_tasks

    def get_all_waiting_tasks(self) -> list[SpiffTask]:
        all_tasks = self.bpmn_process_instance.get_tasks(state=TaskState.ANY_MASK)
        return [t for t in all_tasks if t.state in [TaskState.WAITING]]

    def get_all_ready_or_waiting_tasks(self) -> list[SpiffTask]:
        all_tasks = self.bpmn_process_instance.get_tasks(state=TaskState.ANY_MASK)
        return [t for t in all_tasks if t.state in [TaskState.WAITING, TaskState.READY]]

    def get_task_by_guid(self, task_guid: str) -> SpiffTask | None:
        return self.bpmn_process_instance.get_task_from_id(UUID(task_guid))

    @classmethod
    def get_task_by_bpmn_identifier(cls, bpmn_task_identifier: str, bpmn_process_instance: BpmnWorkflow) -> SpiffTask | None:
        all_tasks = bpmn_process_instance.get_tasks(state=TaskState.ANY_MASK)
        for task in all_tasks:
            if task.task_spec.name == bpmn_task_identifier:
                return task
        return None

    # for debugging, get the full json representation into a file on disk
    def dump_to_disk(self, filename: str = "process.json") -> None:
        with open(filename, "w") as f:
            f.write(json.dumps(self.serialize(), indent=2))

    def remove_spiff_tasks_for_termination(self) -> None:
        start_time = time.time()
        self.bpmn_process_instance.cancel()
        spiff_tasks = self.bpmn_process_instance.get_tasks()

        task_service = TaskService(
            process_instance=self.process_instance_model,
            serializer=BpmnProcessService.serializer,
            bpmn_definition_to_task_definitions_mappings=self.bpmn_definition_to_task_definitions_mappings,
            bpmn_subprocess_mapping=self.bpmn_subprocess_mapping,
            task_model_mapping=self.task_model_mapping,
        )
        task_service.update_all_tasks_from_spiff_tasks(spiff_tasks, [], start_time)

        # we may want to move this to task_service.update_all_tasks_from_spiff_tasks,
        # but not sure it's always good to it.
        # for cancelled tasks, spiff only returns tasks that were cancelled,
        # not the ones that were deleted so we have to find them
        spiff_task_guids = [str(st.id) for st in spiff_tasks]
        tasks_no_longer_in_spiff = TaskModel.query.filter(
            and_(
                TaskModel.process_instance_id == self.process_instance_model.id,
                TaskModel.guid.not_in(spiff_task_guids),  # type: ignore
            )
        ).all()
        for task in tasks_no_longer_in_spiff:
            db.session.delete(task)

        self.save()

    def terminate(self) -> None:
        with suppress(KeyError):
            self.remove_spiff_tasks_for_termination()
        self.process_instance_model.status = "terminated"
        db.session.add(self.process_instance_model)
        ProcessInstanceTmpService.add_event_to_process_instance(
            self.process_instance_model, ProcessInstanceEventType.process_instance_terminated.value
        )
        db.session.commit()

    def suspend(self) -> None:
        self.process_instance_model.status = ProcessInstanceStatus.suspended.value
        db.session.add(self.process_instance_model)
        ProcessInstanceTmpService.add_event_to_process_instance(
            self.process_instance_model, ProcessInstanceEventType.process_instance_suspended.value
        )
        db.session.commit()

    def bring_archived_future_tasks_back_to_life(self) -> None:
        archived_future_tasks = (
            self.process_instance_model.future_tasks_query()
            .filter(FutureTaskModel.archived_for_process_instance_status == True)  # noqa: E712
            .all()
        )
        for archived_future_task in archived_future_tasks:
            archived_future_task.archived_for_process_instance_status = False
            db.session.add(archived_future_task)

    def resume(self) -> None:
        self.process_instance_model.status = ProcessInstanceStatus.waiting.value
        db.session.add(self.process_instance_model)
        self.bring_archived_future_tasks_back_to_life()
        ProcessInstanceTmpService.add_event_to_process_instance(
            self.process_instance_model, ProcessInstanceEventType.process_instance_resumed.value
        )
        db.session.commit()

    def check_all_tasks(self) -> None:
        if current_app.config["SPIFFWORKFLOW_BACKEND_DEBUG_TASK_CONSISTENCY"] is not True:
            return
        tasks = TaskModel.query.filter_by(process_instance_id=self.process_instance_model.id).all()
        missing_child_guids = []
        for task in tasks:
            for child_task_guid in task.properties_json["children"]:
                child_task = TaskModel.query.filter_by(guid=child_task_guid).first()
                if child_task is None:
                    missing_child_guids.append(f"Missing child guid {child_task_guid} for {task.properties_json}")

        if len(missing_child_guids) > 0:
            raise Exception(missing_child_guids)
