# TODO: clean up this service for a clear distinction between it and the process_instance_service
#   where this points to the pi service
import decimal
import json
import logging
import os
import re
import time
import uuid
from collections.abc import Callable
from contextlib import suppress
from datetime import datetime
from datetime import timedelta
from hashlib import sha256
from typing import Any
from typing import NewType
from typing import TypedDict
from uuid import UUID

import _strptime  # type: ignore
import dateparser
import pytz
from flask import current_app
from lxml import etree  # type: ignore
from lxml.etree import XMLSyntaxError  # type: ignore
from RestrictedPython import safe_globals  # type: ignore
from SpiffWorkflow.bpmn.event import BpmnEvent  # type: ignore
from SpiffWorkflow.bpmn.exceptions import WorkflowTaskException  # type: ignore
from SpiffWorkflow.bpmn.parser.ValidationException import ValidationException  # type: ignore
from SpiffWorkflow.bpmn.PythonScriptEngine import PythonScriptEngine  # type: ignore
from SpiffWorkflow.bpmn.PythonScriptEngineEnvironment import BasePythonScriptEngineEnvironment  # type: ignore
from SpiffWorkflow.bpmn.PythonScriptEngineEnvironment import Box
from SpiffWorkflow.bpmn.PythonScriptEngineEnvironment import BoxedTaskDataEnvironment
from SpiffWorkflow.bpmn.serializer.helpers.registry import DefaultRegistry  # type: ignore
from SpiffWorkflow.bpmn.serializer.task_spec import EventBasedGatewayConverter  # type: ignore
from SpiffWorkflow.bpmn.serializer.workflow import BpmnWorkflowSerializer  # type: ignore
from SpiffWorkflow.bpmn.specs.bpmn_process_spec import BpmnProcessSpec  # type: ignore
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow  # type: ignore
from SpiffWorkflow.exceptions import WorkflowException  # type: ignore
from SpiffWorkflow.serializer.exceptions import MissingSpecError  # type: ignore
from SpiffWorkflow.spiff.parser.process import SpiffBpmnParser  # type: ignore
from SpiffWorkflow.spiff.serializer.config import SPIFF_SPEC_CONFIG  # type: ignore
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore
from SpiffWorkflow.task import TaskState
from SpiffWorkflow.util.deep_merge import DeepMerge  # type: ignore
from spiffworkflow_backend.data_stores.typeahead import TypeaheadDataStore
from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.bpmn_process import BpmnProcessModel
from spiffworkflow_backend.models.bpmn_process_definition import BpmnProcessDefinitionModel
from spiffworkflow_backend.models.bpmn_process_definition_relationship import BpmnProcessDefinitionRelationshipModel

# noqa: F401
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.file import File
from spiffworkflow_backend.models.file import FileType
from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.human_task_user import HumanTaskUserModel
from spiffworkflow_backend.models.json_data import JsonDataModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
from spiffworkflow_backend.models.process_instance_event import ProcessInstanceEventType
from spiffworkflow_backend.models.process_instance_metadata import ProcessInstanceMetadataModel
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.models.spec_reference import SpecReferenceCache
from spiffworkflow_backend.models.task import TaskModel
from spiffworkflow_backend.models.task import TaskNotFoundError
from spiffworkflow_backend.models.task_definition import TaskDefinitionModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.scripts.script import Script
from spiffworkflow_backend.services.custom_parser import MyCustomParser
from spiffworkflow_backend.services.element_units_service import ElementUnitsService
from spiffworkflow_backend.services.file_system_service import FileSystemService
from spiffworkflow_backend.services.jinja_service import JinjaHelpers
from spiffworkflow_backend.services.process_instance_queue_service import ProcessInstanceQueueService
from spiffworkflow_backend.services.process_instance_tmp_service import ProcessInstanceTmpService
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.service_task_service import ServiceTaskDelegate
from spiffworkflow_backend.services.spec_file_service import SpecFileService
from spiffworkflow_backend.services.task_service import TaskService
from spiffworkflow_backend.services.user_service import UserService
from spiffworkflow_backend.services.workflow_execution_service import ExecutionStrategy
from spiffworkflow_backend.services.workflow_execution_service import ExecutionStrategyNotConfiguredError
from spiffworkflow_backend.services.workflow_execution_service import SkipOneExecutionStrategy
from spiffworkflow_backend.services.workflow_execution_service import TaskModelSavingDelegate
from spiffworkflow_backend.services.workflow_execution_service import WorkflowExecutionService
from spiffworkflow_backend.services.workflow_execution_service import execution_strategy_named
from spiffworkflow_backend.specs.start_event import StartEvent
from sqlalchemy import and_

StartEvent.register_converter(SPIFF_SPEC_CONFIG)
TypeaheadDataStore.register_converter(SPIFF_SPEC_CONFIG)

# Sorry about all this crap.  I wanted to move this thing to another file, but
# importing a bunch of types causes circular imports.


def _import(name: str, glbls: dict[str, Any], *args: Any) -> None:
    if name not in glbls:
        raise ImportError(f"Import not allowed: {name}", name=name)


class PotentialOwnerIdList(TypedDict):
    potential_owner_ids: list[int]
    lane_assignment_id: int | None


class ProcessInstanceProcessorError(Exception):
    pass


class NoPotentialOwnersForTaskError(Exception):
    pass


class PotentialOwnerUserNotFoundError(Exception):
    pass


class MissingProcessInfoError(Exception):
    pass


class BoxedTaskDataBasedScriptEngineEnvironment(BoxedTaskDataEnvironment):  # type: ignore
    def __init__(self, environment_globals: dict[str, Any]):
        self._last_result: dict[str, Any] = {}
        super().__init__(environment_globals)

    def execute(
        self,
        script: str,
        context: dict[str, Any],
        external_methods: dict[str, Any] | None = None,
    ) -> bool:
        super().execute(script, context, external_methods)
        self._last_result = context
        return True

    def user_defined_state(self, external_methods: dict[str, Any] | None = None) -> dict[str, Any]:
        return {}

    def last_result(self) -> dict[str, Any]:
        return dict(self._last_result.items())

    def clear_state(self) -> None:
        pass

    def preserve_state(self, bpmn_process_instance: BpmnWorkflow) -> None:
        pass

    def restore_state(self, bpmn_process_instance: BpmnWorkflow) -> None:
        pass

    def finalize_result(self, bpmn_process_instance: BpmnWorkflow) -> None:
        pass

    def revise_state_with_task_data(self, task: SpiffTask) -> None:
        pass


class NonTaskDataBasedScriptEngineEnvironment(BasePythonScriptEngineEnvironment):  # type: ignore
    PYTHON_ENVIRONMENT_STATE_KEY = "spiff__python_env_state"

    def __init__(self, environment_globals: dict[str, Any]):
        self.state: dict[str, Any] = {}
        self.non_user_defined_keys = set([*environment_globals.keys()] + ["__builtins__"])
        super().__init__(environment_globals)

    def evaluate(
        self,
        expression: str,
        context: dict[str, Any],
        external_methods: dict[str, Any] | None = None,
    ) -> Any:
        # TODO: once integrated look at the tests that fail without Box
        Box.convert_to_box(context)
        state = {}
        state.update(self.globals)
        state.update(external_methods or {})
        state.update(self.state)
        state.update(context)
        return eval(expression, state)  # noqa

    def execute(
        self,
        script: str,
        context: dict[str, Any],
        external_methods: dict[str, Any] | None = None,
    ) -> bool:
        # TODO: once integrated look at the tests that fail without Box
        # context is task.data
        Box.convert_to_box(context)
        self.state.update(self.globals)
        self.state.update(external_methods or {})
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

            self.state = self.user_defined_state(external_methods)

            # the task data needs to be updated with the current state so data references can be resolved properly.
            # the state will be removed later once the task is completed.
            context.update(self.state)

    def user_defined_state(self, external_methods: dict[str, Any] | None = None) -> dict[str, Any]:
        keys_to_filter = self.non_user_defined_keys
        if external_methods is not None:
            keys_to_filter |= set(external_methods.keys())

        return {k: v for k, v in self.state.items() if k not in keys_to_filter and not callable(v)}

    def last_result(self) -> dict[str, Any]:
        return dict(self.state.items())

    def clear_state(self) -> None:
        self.state = {}

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


# SpiffWorkflow at revision f162aac43af3af18d1a55186aeccea154fb8b05d runs script tasks on ready
# which means that our will_complete_task hook does not have the correct env state when it runs
# so save everything to task data for now until we can figure out a better way to hook into that.
# Revision 6cad2981712bb61eca23af1adfafce02d3277cb9 is the last revision that can run with this.
# class CustomScriptEngineEnvironment(NonTaskDataBasedScriptEngineEnvironment):
class CustomScriptEngineEnvironment(BoxedTaskDataBasedScriptEngineEnvironment):
    pass


class CustomBpmnScriptEngine(PythonScriptEngine):  # type: ignore
    """This is a custom script processor that can be easily injected into Spiff Workflow.

    It will execute python code read in from the bpmn.  It will also make any scripts in the
    scripts directory available for execution.
    """

    def __init__(self, use_restricted_script_engine: bool = True) -> None:
        default_globals = {
            "_strptime": _strptime,
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
            "pytz": pytz,
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

        environment = CustomScriptEngineEnvironment(default_globals)
        super().__init__(environment=environment)

    def __get_augment_methods(self, task: SpiffTask | None) -> dict[str, Callable]:
        tld = current_app.config.get("THREAD_LOCAL_DATA")
        process_model_identifier = None
        process_instance_id = None
        if tld:
            if hasattr(tld, "process_model_identifier"):
                process_model_identifier = tld.process_model_identifier
            if hasattr(tld, "process_instance_id"):
                process_instance_id = tld.process_instance_id
        script_attributes_context = ScriptAttributesContext(
            task=task,
            environment_identifier=current_app.config["ENV_IDENTIFIER"],
            process_instance_id=process_instance_id,
            process_model_identifier=process_model_identifier,
        )
        return Script.generate_augmented_list(script_attributes_context)

    def evaluate(
        self,
        task: SpiffTask,
        expression: str,
        external_methods: dict[str, Any] | None = None,
    ) -> Any:
        return self._evaluate(expression, task.data, task, external_methods)

    def _evaluate(
        self,
        expression: str,
        context: dict[str, Box | str],
        task: SpiffTask | None = None,
        external_methods: dict[str, Any] | None = None,
    ) -> Any:
        methods = self.__get_augment_methods(task)
        if external_methods:
            methods.update(external_methods)

        """Evaluate the given expression, within the context of the given task and return the result."""
        try:
            return super()._evaluate(expression, context, external_methods=methods)
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

    def execute(self, task: SpiffTask, script: str, external_methods: Any = None) -> bool:
        try:
            # reset failing task just in case
            methods = self.__get_augment_methods(task)
            if external_methods:
                methods.update(external_methods)
            # do not run script if it is blank
            if script:
                super().execute(task, script, methods)
            return True
        except WorkflowException as e:
            raise e
        except Exception as e:
            raise self.create_task_exec_exception(task, script, e) from e

    def call_service(
        self,
        operation_name: str,
        operation_params: dict[str, Any],
        task_data: dict[str, Any],
    ) -> Any:
        return ServiceTaskDelegate.call_connector(operation_name, operation_params, task_data)


IdToBpmnProcessSpecMapping = NewType("IdToBpmnProcessSpecMapping", dict[str, BpmnProcessSpec])


class ProcessInstanceProcessor:
    _default_script_engine = CustomBpmnScriptEngine()
    SERIALIZER_VERSION = "1.0-spiffworkflow-backend"

    wf_spec_converter = BpmnWorkflowSerializer.configure_workflow_spec_converter(SPIFF_SPEC_CONFIG)
    _serializer = BpmnWorkflowSerializer(wf_spec_converter, version=SERIALIZER_VERSION)
    _event_serializer = EventBasedGatewayConverter(wf_spec_converter)

    PROCESS_INSTANCE_ID_KEY = "process_instance_id"
    VALIDATION_PROCESS_KEY = "validate_only"

    # __init__ calls these helpers:
    #   * get_spec, which returns a spec and any subprocesses (as IdToBpmnProcessSpecMapping dict)
    #   * __get_bpmn_process_instance, which takes spec and subprocesses and instantiates and returns a BpmnWorkflow
    def __init__(
        self,
        process_instance_model: ProcessInstanceModel,
        validate_only: bool = False,
        script_engine: PythonScriptEngine | None = None,
    ) -> None:
        """Create a Workflow Processor based on the serialized information available in the process_instance model."""
        self._script_engine = script_engine or self.__class__._default_script_engine
        self.setup_processor_with_process_instance(
            process_instance_model=process_instance_model, validate_only=validate_only
        )

    def setup_processor_with_process_instance(
        self, process_instance_model: ProcessInstanceModel, validate_only: bool = False
    ) -> None:
        tld = current_app.config["THREAD_LOCAL_DATA"]
        tld.process_instance_id = process_instance_model.id

        # we want this to be the fully qualified path to the process model including all group subcomponents
        current_app.config["THREAD_LOCAL_DATA"].process_model_identifier = (
            f"{process_instance_model.process_model_identifier}"
        )

        self.process_instance_model = process_instance_model
        bpmn_process_spec = None
        self.full_bpmn_process_dict: dict = {}

        # this caches the bpmn_process_definition_identifier and task_identifier back to the bpmn_process_id
        # in the database. This is to cut down on database queries while adding new tasks to the database.
        # Structure:
        #   { "[[BPMN_PROCESS_DEFINITION_IDENTIFIER]]": {
        #       "[[TASK_IDENTIFIER]]": [[TASK_DEFINITION]],
        #       "bpmn_process_definition": [[BPMN_PROCESS_DEFINITION]] }
        #   }
        # To use from a spiff_task:
        #   [spiff_task.workflow.spec.name][spiff_task.task_spec.name]
        self.bpmn_definition_to_task_definitions_mappings: dict = {}

        subprocesses: IdToBpmnProcessSpecMapping | None = None
        if process_instance_model.bpmn_process_definition_id is None:
            (
                bpmn_process_spec,
                subprocesses,
            ) = ProcessInstanceProcessor.get_process_model_and_subprocesses(
                process_instance_model.process_model_identifier
            )

        self.process_model_identifier = process_instance_model.process_model_identifier
        self.process_model_display_name = process_instance_model.process_model_display_name

        try:
            (
                self.bpmn_process_instance,
                self.full_bpmn_process_dict,
                self.bpmn_definition_to_task_definitions_mappings,
            ) = self.__get_bpmn_process_instance(
                process_instance_model,
                bpmn_process_spec,
                validate_only,
                subprocesses=subprocesses,
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
    def get_process_model_and_subprocesses(
        cls, process_model_identifier: str
    ) -> tuple[BpmnProcessSpec, IdToBpmnProcessSpecMapping]:
        process_model_info = ProcessModelService.get_process_model(process_model_identifier)
        if process_model_info is None:
            raise (
                ApiError(
                    "process_model_not_found",
                    f"The given process model was not found: {process_model_identifier}.",
                )
            )
        spec_files = FileSystemService.get_files(process_model_info)
        return cls.get_spec(spec_files, process_model_info)

    @classmethod
    def get_bpmn_process_instance_from_process_model(cls, process_model_identifier: str) -> BpmnWorkflow:
        (bpmn_process_spec, subprocesses) = cls.get_process_model_and_subprocesses(
            process_model_identifier,
        )
        bpmn_process_instance = cls.get_bpmn_process_instance_from_workflow_spec(bpmn_process_spec, subprocesses)
        cls.set_script_engine(bpmn_process_instance)
        return bpmn_process_instance

    @staticmethod
    def set_script_engine(
        bpmn_process_instance: BpmnWorkflow, script_engine: PythonScriptEngine | None = None
    ) -> None:
        script_engine_to_use = script_engine or ProcessInstanceProcessor._default_script_engine
        script_engine_to_use.environment.restore_state(bpmn_process_instance)
        bpmn_process_instance.script_engine = script_engine_to_use

    def preserve_script_engine_state(self) -> None:
        self._script_engine.environment.preserve_state(self.bpmn_process_instance)

    @classmethod
    def _update_bpmn_definition_mappings(
        cls,
        bpmn_definition_to_task_definitions_mappings: dict,
        bpmn_process_definition_identifier: str,
        task_definition: TaskDefinitionModel | None = None,
        bpmn_process_definition: BpmnProcessDefinitionModel | None = None,
    ) -> None:
        if bpmn_process_definition_identifier not in bpmn_definition_to_task_definitions_mappings:
            bpmn_definition_to_task_definitions_mappings[bpmn_process_definition_identifier] = {}

        if task_definition is not None:
            bpmn_definition_to_task_definitions_mappings[bpmn_process_definition_identifier][
                task_definition.bpmn_identifier
            ] = task_definition

        if bpmn_process_definition is not None:
            bpmn_definition_to_task_definitions_mappings[bpmn_process_definition_identifier][
                "bpmn_process_definition"
            ] = bpmn_process_definition

    @classmethod
    def _get_definition_dict_for_bpmn_process_definition(
        cls,
        bpmn_process_definition: BpmnProcessDefinitionModel,
        bpmn_definition_to_task_definitions_mappings: dict,
    ) -> dict:
        cls._update_bpmn_definition_mappings(
            bpmn_definition_to_task_definitions_mappings,
            bpmn_process_definition.bpmn_identifier,
            bpmn_process_definition=bpmn_process_definition,
        )
        task_definitions = TaskDefinitionModel.query.filter_by(
            bpmn_process_definition_id=bpmn_process_definition.id
        ).all()
        bpmn_process_definition_dict: dict = bpmn_process_definition.properties_json
        bpmn_process_definition_dict["task_specs"] = {}
        for task_definition in task_definitions:
            bpmn_process_definition_dict["task_specs"][
                task_definition.bpmn_identifier
            ] = task_definition.properties_json
            cls._update_bpmn_definition_mappings(
                bpmn_definition_to_task_definitions_mappings,
                bpmn_process_definition.bpmn_identifier,
                task_definition=task_definition,
            )
        return bpmn_process_definition_dict

    @classmethod
    def _set_definition_dict_for_bpmn_subprocess_definitions(
        cls,
        bpmn_process_definition: BpmnProcessDefinitionModel,
        spiff_bpmn_process_dict: dict,
        bpmn_definition_to_task_definitions_mappings: dict,
    ) -> None:
        # find all child subprocesses of a process
        bpmn_process_subprocess_definitions = (
            BpmnProcessDefinitionModel.query.join(
                BpmnProcessDefinitionRelationshipModel,
                BpmnProcessDefinitionModel.id
                == BpmnProcessDefinitionRelationshipModel.bpmn_process_definition_child_id,
            )
            .filter_by(bpmn_process_definition_parent_id=bpmn_process_definition.id)
            .all()
        )

        bpmn_subprocess_definition_bpmn_identifiers = {}
        for bpmn_subprocess_definition in bpmn_process_subprocess_definitions:
            cls._update_bpmn_definition_mappings(
                bpmn_definition_to_task_definitions_mappings,
                bpmn_subprocess_definition.bpmn_identifier,
                bpmn_process_definition=bpmn_subprocess_definition,
            )
            bpmn_process_definition_dict: dict = bpmn_subprocess_definition.properties_json
            spiff_bpmn_process_dict["subprocess_specs"][
                bpmn_subprocess_definition.bpmn_identifier
            ] = bpmn_process_definition_dict
            spiff_bpmn_process_dict["subprocess_specs"][bpmn_subprocess_definition.bpmn_identifier]["task_specs"] = {}
            bpmn_subprocess_definition_bpmn_identifiers[bpmn_subprocess_definition.id] = (
                bpmn_subprocess_definition.bpmn_identifier
            )

        task_definitions = TaskDefinitionModel.query.filter(
            TaskDefinitionModel.bpmn_process_definition_id.in_(  # type: ignore
                bpmn_subprocess_definition_bpmn_identifiers.keys()
            )
        ).all()
        for task_definition in task_definitions:
            bpmn_subprocess_definition_bpmn_identifier = bpmn_subprocess_definition_bpmn_identifiers[
                task_definition.bpmn_process_definition_id
            ]
            cls._update_bpmn_definition_mappings(
                bpmn_definition_to_task_definitions_mappings,
                bpmn_subprocess_definition_bpmn_identifier,
                task_definition=task_definition,
            )
            spiff_bpmn_process_dict["subprocess_specs"][bpmn_subprocess_definition_bpmn_identifier]["task_specs"][
                task_definition.bpmn_identifier
            ] = task_definition.properties_json

    @classmethod
    def _get_bpmn_process_dict(cls, bpmn_process: BpmnProcessModel, get_tasks: bool = False) -> dict:
        json_data = JsonDataModel.query.filter_by(hash=bpmn_process.json_data_hash).first()
        bpmn_process_dict = {"data": json_data.data, "tasks": {}}
        bpmn_process_dict.update(bpmn_process.properties_json)
        if get_tasks:
            tasks = TaskModel.query.filter_by(bpmn_process_id=bpmn_process.id).all()
            cls._get_tasks_dict(tasks, bpmn_process_dict)
        return bpmn_process_dict

    @classmethod
    def _get_tasks_dict(
        cls,
        tasks: list[TaskModel],
        spiff_bpmn_process_dict: dict,
        bpmn_subprocess_id_to_guid_mappings: dict | None = None,
    ) -> None:
        json_data_hashes = set()
        for task in tasks:
            json_data_hashes.add(task.json_data_hash)
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
            tasks_dict[task.guid]["data"] = json_data_mappings[task.json_data_hash]

    @classmethod
    def _get_full_bpmn_process_dict(
        cls,
        process_instance_model: ProcessInstanceModel,
        bpmn_definition_to_task_definitions_mappings: dict,
    ) -> dict:
        if process_instance_model.bpmn_process_definition_id is None:
            return {}

        spiff_bpmn_process_dict: dict = {
            "serializer_version": process_instance_model.spiff_serializer_version,
            "spec": {},
            "subprocess_specs": {},
            "subprocesses": {},
        }
        bpmn_process_definition = process_instance_model.bpmn_process_definition
        if bpmn_process_definition is not None:
            spiff_bpmn_process_dict["spec"] = cls._get_definition_dict_for_bpmn_process_definition(
                bpmn_process_definition,
                bpmn_definition_to_task_definitions_mappings,
            )
            cls._set_definition_dict_for_bpmn_subprocess_definitions(
                bpmn_process_definition,
                spiff_bpmn_process_dict,
                bpmn_definition_to_task_definitions_mappings,
            )

            #
            # see if we have any cached element units and if so step on the spec and subprocess_specs.
            # in the early stages of development this will return the full workflow when the feature
            # flag is set to on. as time goes we will need to think about how this plays in with the
            # bpmn definition tables more.
            #

            element_unit_process_dict = None
            full_process_model_hash = bpmn_process_definition.full_process_model_hash

            if full_process_model_hash is not None:
                element_unit_process_dict = ElementUnitsService.workflow_from_cached_element_unit(
                    full_process_model_hash,
                    bpmn_process_definition.bpmn_identifier,
                    bpmn_process_definition.bpmn_identifier,
                )
            if element_unit_process_dict is not None:
                spiff_bpmn_process_dict["spec"] = element_unit_process_dict["spec"]
                spiff_bpmn_process_dict["subprocess_specs"] = element_unit_process_dict["subprocess_specs"]

            bpmn_process = process_instance_model.bpmn_process
            if bpmn_process is not None:
                single_bpmn_process_dict = cls._get_bpmn_process_dict(bpmn_process, get_tasks=True)
                spiff_bpmn_process_dict.update(single_bpmn_process_dict)

                bpmn_subprocesses = BpmnProcessModel.query.filter_by(top_level_process_id=bpmn_process.id).all()
                bpmn_subprocess_id_to_guid_mappings = {}
                for bpmn_subprocess in bpmn_subprocesses:
                    subprocess_identifier = bpmn_subprocess.bpmn_process_definition.bpmn_identifier
                    if subprocess_identifier not in spiff_bpmn_process_dict["subprocess_specs"]:
                        current_app.logger.info(f"Deferring subprocess spec: '{subprocess_identifier}'")
                        continue
                    bpmn_subprocess_id_to_guid_mappings[bpmn_subprocess.id] = bpmn_subprocess.guid
                    single_bpmn_process_dict = cls._get_bpmn_process_dict(bpmn_subprocess)
                    spiff_bpmn_process_dict["subprocesses"][bpmn_subprocess.guid] = single_bpmn_process_dict

                tasks = TaskModel.query.filter(
                    TaskModel.bpmn_process_id.in_(bpmn_subprocess_id_to_guid_mappings.keys())  # type: ignore
                ).all()
                cls._get_tasks_dict(tasks, spiff_bpmn_process_dict, bpmn_subprocess_id_to_guid_mappings)

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
    def get_bpmn_process_instance_from_workflow_spec(
        spec: BpmnProcessSpec,
        subprocesses: IdToBpmnProcessSpecMapping | None = None,
    ) -> BpmnWorkflow:
        bpmn_process_instance = BpmnWorkflow(
            spec,
            subprocess_specs=subprocesses,
        )
        return bpmn_process_instance

    @staticmethod
    def __get_bpmn_process_instance(
        process_instance_model: ProcessInstanceModel,
        spec: BpmnProcessSpec | None = None,
        validate_only: bool = False,
        subprocesses: IdToBpmnProcessSpecMapping | None = None,
    ) -> tuple[BpmnWorkflow, dict, dict]:
        full_bpmn_process_dict = {}
        bpmn_definition_to_task_definitions_mappings: dict = {}
        if process_instance_model.bpmn_process_definition_id is not None:
            # turn off logging to avoid duplicated spiff logs
            spiff_logger = logging.getLogger("spiff")
            original_spiff_logger_log_level = spiff_logger.level
            spiff_logger.setLevel(logging.WARNING)

            try:
                full_bpmn_process_dict = ProcessInstanceProcessor._get_full_bpmn_process_dict(
                    process_instance_model,
                    bpmn_definition_to_task_definitions_mappings,
                )
                bpmn_process_instance = ProcessInstanceProcessor._serializer.workflow_from_dict(full_bpmn_process_dict)
            except Exception as err:
                raise err
            finally:
                spiff_logger.setLevel(original_spiff_logger_log_level)
        else:
            bpmn_process_instance = ProcessInstanceProcessor.get_bpmn_process_instance_from_workflow_spec(
                spec, subprocesses
            )
            bpmn_process_instance.data[ProcessInstanceProcessor.VALIDATION_PROCESS_KEY] = validate_only

        # run _predict to ensure tasks are predicted to add back in LIKELY and MAYBE tasks
        bpmn_process_instance._predict()
        return (
            bpmn_process_instance,
            full_bpmn_process_dict,
            bpmn_definition_to_task_definitions_mappings,
        )

    def add_data_to_bpmn_process_instance(self, data: dict) -> None:
        # if we do not use a deep merge, then the data does not end up on the object for some reason
        self.bpmn_process_instance.data = DeepMerge.merge(self.bpmn_process_instance.data, data)

    def raise_if_no_potential_owners(self, potential_owner_ids: list[int], message: str) -> None:
        if not potential_owner_ids:
            raise NoPotentialOwnersForTaskError(message)

    def get_potential_owner_ids_from_task(self, task: SpiffTask) -> PotentialOwnerIdList:
        task_spec = task.task_spec
        task_lane = "process_initiator"
        if task_spec.lane is not None and task_spec.lane != "":
            task_lane = task_spec.lane

        potential_owner_ids = []
        lane_assignment_id = None
        if re.match(r"(process.?)initiator", task_lane, re.IGNORECASE):
            potential_owner_ids = [self.process_instance_model.process_initiator_id]
        else:
            group_model = GroupModel.query.filter_by(identifier=task_lane).first()
            if group_model is not None:
                lane_assignment_id = group_model.id
            if "lane_owners" in task.data and task_lane in task.data["lane_owners"]:
                for username in task.data["lane_owners"][task_lane]:
                    lane_owner_user = UserModel.query.filter_by(username=username).first()
                    if lane_owner_user is not None:
                        potential_owner_ids.append(lane_owner_user.id)
                self.raise_if_no_potential_owners(
                    potential_owner_ids,
                    (
                        "No users found in task data lane owner list for lane:"
                        f" {task_lane}. The user list used:"
                        f" {task.data['lane_owners'][task_lane]}"
                    ),
                )
            else:
                if group_model is None:
                    raise (
                        NoPotentialOwnersForTaskError(f"Could not find a group with name matching lane: {task_lane}")
                    )
                potential_owner_ids = [i.user_id for i in group_model.user_group_assignments]
                self.raise_if_no_potential_owners(
                    potential_owner_ids,
                    f"Could not find any users in group to assign to lane: {task_lane}",
                )

        return {
            "potential_owner_ids": potential_owner_ids,
            "lane_assignment_id": lane_assignment_id,
        }

    def extract_metadata(self, process_model_info: ProcessModelInfo) -> None:
        metadata_extraction_paths = process_model_info.metadata_extraction_paths
        if metadata_extraction_paths is None:
            return
        if len(metadata_extraction_paths) <= 0:
            return

        current_data = self.get_current_data()
        for metadata_extraction_path in metadata_extraction_paths:
            key = metadata_extraction_path["key"]
            path = metadata_extraction_path["path"]
            path_segments = path.split(".")
            data_for_key = current_data
            for path_segment in path_segments:
                if path_segment in data_for_key:
                    data_for_key = data_for_key[path_segment]
                else:
                    data_for_key = None  # type: ignore
                    break

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
                pim.value = str(data_for_key)[0:255]
                db.session.add(pim)
                db.session.commit()

    def _store_bpmn_process_definition(
        self,
        process_bpmn_properties: dict,
        bpmn_process_definition_parent: BpmnProcessDefinitionModel | None = None,
        store_bpmn_definition_mappings: bool = False,
        full_bpmn_spec_dict: dict | None = None,
    ) -> BpmnProcessDefinitionModel:
        process_bpmn_identifier = process_bpmn_properties["name"]
        process_bpmn_name = process_bpmn_properties["description"]

        bpmn_process_definition: BpmnProcessDefinitionModel | None = None
        single_process_hash = sha256(json.dumps(process_bpmn_properties, sort_keys=True).encode("utf8")).hexdigest()
        full_process_model_hash = None
        if full_bpmn_spec_dict is not None:
            full_process_model_hash = sha256(
                json.dumps(full_bpmn_spec_dict, sort_keys=True).encode("utf8")
            ).hexdigest()
            bpmn_process_definition = BpmnProcessDefinitionModel.query.filter_by(
                full_process_model_hash=full_process_model_hash
            ).first()
        else:
            bpmn_process_definition = BpmnProcessDefinitionModel.query.filter_by(
                single_process_hash=single_process_hash
            ).first()

        if bpmn_process_definition is None:
            task_specs = process_bpmn_properties.pop("task_specs")
            bpmn_process_definition = BpmnProcessDefinitionModel(
                single_process_hash=single_process_hash,
                full_process_model_hash=full_process_model_hash,
                bpmn_identifier=process_bpmn_identifier,
                bpmn_name=process_bpmn_name,
                properties_json=process_bpmn_properties,
            )
            db.session.add(bpmn_process_definition)
            self._update_bpmn_definition_mappings(
                self.bpmn_definition_to_task_definitions_mappings,
                bpmn_process_definition.bpmn_identifier,
                bpmn_process_definition=bpmn_process_definition,
            )
            for task_bpmn_identifier, task_bpmn_properties in task_specs.items():
                task_bpmn_name = task_bpmn_properties["bpmn_name"]
                task_definition = TaskDefinitionModel(
                    bpmn_process_definition=bpmn_process_definition,
                    bpmn_identifier=task_bpmn_identifier,
                    bpmn_name=task_bpmn_name,
                    properties_json=task_bpmn_properties,
                    typename=task_bpmn_properties["typename"],
                )
                db.session.add(task_definition)
                if store_bpmn_definition_mappings:
                    self._update_bpmn_definition_mappings(
                        self.bpmn_definition_to_task_definitions_mappings,
                        process_bpmn_identifier,
                        task_definition=task_definition,
                    )
        elif store_bpmn_definition_mappings:
            # this should only ever happen when new process instances use a pre-existing bpmn process definitions
            # otherwise this should get populated on processor initialization
            self._update_bpmn_definition_mappings(
                self.bpmn_definition_to_task_definitions_mappings,
                process_bpmn_identifier,
                bpmn_process_definition=bpmn_process_definition,
            )
            task_definitions = TaskDefinitionModel.query.filter_by(
                bpmn_process_definition_id=bpmn_process_definition.id
            ).all()
            for task_definition in task_definitions:
                self._update_bpmn_definition_mappings(
                    self.bpmn_definition_to_task_definitions_mappings,
                    process_bpmn_identifier,
                    task_definition=task_definition,
                )

        if bpmn_process_definition_parent is not None:
            bpmn_process_definition_relationship = BpmnProcessDefinitionRelationshipModel.query.filter_by(
                bpmn_process_definition_parent_id=bpmn_process_definition_parent.id,
                bpmn_process_definition_child_id=bpmn_process_definition.id,
            ).first()
            if bpmn_process_definition_relationship is None:
                bpmn_process_definition_relationship = BpmnProcessDefinitionRelationshipModel(
                    bpmn_process_definition_parent_id=bpmn_process_definition_parent.id,
                    bpmn_process_definition_child_id=bpmn_process_definition.id,
                )
                db.session.add(bpmn_process_definition_relationship)
        return bpmn_process_definition

    def _add_bpmn_process_definitions(self) -> None:
        """Adds serialized_bpmn_definition records to the db session.

        Expects the calling method to commit it.
        """
        if self.process_instance_model.bpmn_process_definition_id is not None:
            return None

        # we may have to already process bpmn_defintions if we ever care about the Root task again
        bpmn_dict = self.serialize()
        bpmn_dict_keys = ("spec", "subprocess_specs", "serializer_version")
        bpmn_spec_dict = {}
        for bpmn_key in bpmn_dict.keys():
            if bpmn_key in bpmn_dict_keys:
                bpmn_spec_dict[bpmn_key] = bpmn_dict[bpmn_key]

        # store only if mappings is currently empty. this also would mean this is a new instance that has never saved before
        store_bpmn_definition_mappings = not self.bpmn_definition_to_task_definitions_mappings
        bpmn_process_definition_parent = self._store_bpmn_process_definition(
            bpmn_spec_dict["spec"],
            store_bpmn_definition_mappings=store_bpmn_definition_mappings,
            full_bpmn_spec_dict=bpmn_spec_dict,
        )
        for process_bpmn_properties in bpmn_spec_dict["subprocess_specs"].values():
            self._store_bpmn_process_definition(
                process_bpmn_properties,
                bpmn_process_definition_parent,
                store_bpmn_definition_mappings=store_bpmn_definition_mappings,
            )
        self.process_instance_model.bpmn_process_definition = bpmn_process_definition_parent

        #
        # builds and caches the element units for the parent bpmn process defintion. these
        # element units can then be queried using the same hash for later execution.
        #
        # TODO: this seems to be run each time a process instance is started, so element
        # units will only be queried after a save/resume point. the hash used as the key
        # can be anything, so possibly some hash of all files required to form the process
        # definition and their hashes could be used? Not sure how that plays in with the
        # bpmn_process_defintion hash though.
        #

        # TODO: first time through for an instance the bpmn_spec_dict seems to get mutated,
        # so for now we don't seed the cache until the second instance. not immediately a
        # problem and can be part of the larger discussion mentioned in the TODO above.

        full_process_model_hash = bpmn_process_definition_parent.full_process_model_hash

        if full_process_model_hash is not None and "task_specs" in bpmn_spec_dict["spec"]:
            ElementUnitsService.cache_element_units_for_workflow(full_process_model_hash, bpmn_spec_dict)

    def save(self) -> None:
        """Saves the current state of this processor to the database."""
        self.process_instance_model.spiff_serializer_version = self.SERIALIZER_VERSION

        self.process_instance_model.status = self.get_status().value
        current_app.logger.debug(
            f"the_status: {self.process_instance_model.status} for instance {self.process_instance_model.id}"
        )

        if self.process_instance_model.start_in_seconds is None:
            self.process_instance_model.start_in_seconds = round(time.time())

        if self.process_instance_model.end_in_seconds is None:
            if self.bpmn_process_instance.is_completed():
                self.process_instance_model.end_in_seconds = round(time.time())

        db.session.add(self.process_instance_model)
        db.session.commit()

        human_tasks = HumanTaskModel.query.filter_by(
            process_instance_id=self.process_instance_model.id, completed=False
        ).all()
        ready_or_waiting_tasks = self.get_all_ready_or_waiting_tasks()

        process_model_display_name = ""
        process_model_info = ProcessModelService.get_process_model(
            self.process_instance_model.process_model_identifier
        )
        if process_model_info is not None:
            process_model_display_name = process_model_info.display_name

        self.extract_metadata(process_model_info)

        for ready_or_waiting_task in ready_or_waiting_tasks:
            # filter out non-usertasks
            task_spec = ready_or_waiting_task.task_spec
            if task_spec.manual:
                potential_owner_hash = self.get_potential_owner_ids_from_task(ready_or_waiting_task)
                extensions = task_spec.extensions

                # in the xml, it's the id attribute. this identifies the process where the activity lives.
                # if it's in a subprocess, it's the inner process.
                bpmn_process_identifier = ready_or_waiting_task.workflow.spec.name

                form_file_name = None
                ui_form_file_name = None
                if "properties" in extensions:
                    properties = extensions["properties"]
                    if "formJsonSchemaFilename" in properties:
                        form_file_name = properties["formJsonSchemaFilename"]
                    if "formUiSchemaFilename" in properties:
                        ui_form_file_name = properties["formUiSchemaFilename"]

                human_task = None
                for at in human_tasks:
                    if at.task_id == str(ready_or_waiting_task.id):
                        human_task = at
                        human_tasks.remove(at)

                if human_task is None:
                    task_guid = str(ready_or_waiting_task.id)
                    task_model = TaskModel.query.filter_by(guid=task_guid).first()
                    if task_model is None:
                        raise TaskNotFoundError(f"Could not find task for human task with guid: {task_guid}")

                    human_task = HumanTaskModel(
                        process_instance_id=self.process_instance_model.id,
                        process_model_display_name=process_model_display_name,
                        bpmn_process_identifier=bpmn_process_identifier,
                        form_file_name=form_file_name,
                        ui_form_file_name=ui_form_file_name,
                        task_model_id=task_model.id,
                        task_id=task_guid,
                        task_name=ready_or_waiting_task.task_spec.bpmn_id,
                        task_title=ready_or_waiting_task.task_spec.bpmn_name,
                        task_type=ready_or_waiting_task.task_spec.__class__.__name__,
                        task_status=ready_or_waiting_task.get_state_name(),
                        lane_assignment_id=potential_owner_hash["lane_assignment_id"],
                    )
                    db.session.add(human_task)

                    for potential_owner_id in potential_owner_hash["potential_owner_ids"]:
                        human_task_user = HumanTaskUserModel(user_id=potential_owner_id, human_task=human_task)
                        db.session.add(human_task_user)

                    db.session.commit()

        if len(human_tasks) > 0:
            for at in human_tasks:
                at.completed = True
                db.session.add(at)
            db.session.commit()

    def serialize_task_spec(self, task_spec: SpiffTask) -> Any:
        """Get a serialized version of a task spec."""
        # The task spec is NOT actually a SpiffTask, it is the task spec attached to a SpiffTask
        # Not sure why mypy accepts this but whatever.
        return self._serializer.spec_converter.convert(task_spec)

    def send_bpmn_event(self, event_data: dict[str, Any]) -> None:
        """Send an event to the workflow."""
        payload = event_data.pop("payload", None)
        event_definition = self._event_serializer.registry.restore(event_data)
        bpmn_event = BpmnEvent(
            event_definition=event_definition,
            payload=payload,
        )
        try:
            self.bpmn_process_instance.send_event(bpmn_event)
        except Exception as e:
            print(e)

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
                f"Manually skipping Human Task {spiff_task.task_spec.name} of process"
                f" instance {self.process_instance_model.id}"
            )
            human_task = HumanTaskModel.query.filter_by(task_id=task_id).first()
            self.complete_task(spiff_task, human_task=human_task, user=user)
        elif execute:
            current_app.logger.info(
                f"Manually executing Task {spiff_task.task_spec.name} of process"
                f" instance {self.process_instance_model.id}"
            )
            self.do_engine_steps(save=True, execution_strategy_name="one_at_a_time")
        else:
            current_app.logger.info(f"Skipped task {spiff_task.task_spec.name}", extra=spiff_task.log_info())
            task_model_delegate = TaskModelSavingDelegate(
                serializer=self._serializer,
                process_instance=self.process_instance_model,
                bpmn_definition_to_task_definitions_mappings=self.bpmn_definition_to_task_definitions_mappings,
            )
            execution_strategy = SkipOneExecutionStrategy(
                task_model_delegate, self.lazy_load_subprocess_specs, {"spiff_task": spiff_task}
            )
            self.do_engine_steps(save=True, execution_strategy=execution_strategy)

        spiff_tasks = self.bpmn_process_instance.get_tasks()
        task_service = TaskService(
            process_instance=self.process_instance_model,
            serializer=self._serializer,
            bpmn_definition_to_task_definitions_mappings=self.bpmn_definition_to_task_definitions_mappings,
        )
        task_service.update_all_tasks_from_spiff_tasks(spiff_tasks, [], start_time)
        ProcessInstanceTmpService.add_event_to_process_instance(
            self.process_instance_model, event_type, task_guid=task_id
        )

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
        processor = ProcessInstanceProcessor(process_instance)
        deleted_tasks = processor.bpmn_process_instance.reset_from_task_id(UUID(to_task_guid))
        spiff_tasks = processor.bpmn_process_instance.get_tasks()

        task_service = TaskService(
            process_instance=processor.process_instance_model,
            serializer=processor._serializer,
            bpmn_definition_to_task_definitions_mappings=processor.bpmn_definition_to_task_definitions_mappings,
        )
        task_service.update_all_tasks_from_spiff_tasks(spiff_tasks, deleted_tasks, start_time)

        # Save the process
        processor.save()
        processor.suspend()

    @staticmethod
    def get_parser() -> MyCustomParser:
        parser = MyCustomParser()
        return parser

    @staticmethod
    def backfill_missing_spec_reference_records(
        bpmn_process_identifier: str,
    ) -> str | None:
        process_models = ProcessModelService.get_process_models(recursive=True)
        for process_model in process_models:
            try:
                refs = SpecFileService.reference_map(SpecFileService.get_references_for_process(process_model))
                bpmn_process_identifiers = refs.keys()
                if bpmn_process_identifier in bpmn_process_identifiers:
                    SpecFileService.update_process_cache(refs[bpmn_process_identifier])
                    return FileSystemService.full_path_to_process_model_file(process_model)
            except Exception:
                current_app.logger.warning("Failed to parse process ", process_model.id)
        return None

    @staticmethod
    def bpmn_file_full_path_from_bpmn_process_identifier(
        bpmn_process_identifier: str,
    ) -> str:
        if bpmn_process_identifier is None:
            raise ValueError(
                "bpmn_file_full_path_from_bpmn_process_identifier: bpmn_process_identifier is unexpectedly None"
            )

        spec_reference = SpecReferenceCache.query.filter_by(identifier=bpmn_process_identifier, type="process").first()
        bpmn_file_full_path = None
        if spec_reference is None:
            bpmn_file_full_path = ProcessInstanceProcessor.backfill_missing_spec_reference_records(
                bpmn_process_identifier
            )
        else:
            bpmn_file_full_path = os.path.join(
                FileSystemService.root_path(),
                spec_reference.relative_path,
            )
        if bpmn_file_full_path is None:
            raise (
                ApiError(
                    error_code="could_not_find_bpmn_process_identifier",
                    message="Could not find the the given bpmn process identifier from any sources: %s"
                    % bpmn_process_identifier,
                )
            )
        return os.path.abspath(bpmn_file_full_path)

    @staticmethod
    def update_spiff_parser_with_all_process_dependency_files(
        parser: SpiffBpmnParser,
        processed_identifiers: set[str] | None = None,
    ) -> None:
        if processed_identifiers is None:
            processed_identifiers = set()
        processor_dependencies = parser.get_process_dependencies()

        # since get_process_dependencies() returns a set with None sometimes, we need to remove it
        processor_dependencies = processor_dependencies - {None}

        processor_dependencies_new = processor_dependencies - processed_identifiers
        bpmn_process_identifiers_in_parser = parser.get_process_ids()

        new_bpmn_files = set()
        for bpmn_process_identifier in processor_dependencies_new:
            # ignore identifiers that spiff already knows about
            if bpmn_process_identifier in bpmn_process_identifiers_in_parser:
                continue

            new_bpmn_file_full_path = ProcessInstanceProcessor.bpmn_file_full_path_from_bpmn_process_identifier(
                bpmn_process_identifier
            )
            new_bpmn_files.add(new_bpmn_file_full_path)
            dmn_file_glob = os.path.join(os.path.dirname(new_bpmn_file_full_path), "*.dmn")
            parser.add_dmn_files_by_glob(dmn_file_glob)
            processed_identifiers.add(bpmn_process_identifier)

        if new_bpmn_files:
            parser.add_bpmn_files(new_bpmn_files)
            ProcessInstanceProcessor.update_spiff_parser_with_all_process_dependency_files(
                parser, processed_identifiers
            )

    @staticmethod
    def get_spec(
        files: list[File], process_model_info: ProcessModelInfo
    ) -> tuple[BpmnProcessSpec, IdToBpmnProcessSpecMapping]:
        """Returns a SpiffWorkflow specification for the given process_instance spec, using the files provided."""
        parser = ProcessInstanceProcessor.get_parser()

        for file in files:
            data = SpecFileService.get_data(process_model_info, file.name)
            try:
                if file.type == FileType.bpmn.value:
                    bpmn: etree.Element = SpecFileService.get_etree_from_xml_bytes(data)
                    parser.add_bpmn_xml(bpmn, filename=file.name)
                elif file.type == FileType.dmn.value:
                    dmn: etree.Element = SpecFileService.get_etree_from_xml_bytes(data)
                    parser.add_dmn_xml(dmn, filename=file.name)
            except XMLSyntaxError as xse:
                raise ApiError(
                    error_code="invalid_xml",
                    message=f"'{file.name}' is not a valid xml file." + str(xse),
                ) from xse
        if process_model_info.primary_process_id is None or process_model_info.primary_process_id == "":
            raise (
                ApiError(
                    error_code="no_primary_bpmn_error",
                    message="There is no primary BPMN process id defined for process_model %s" % process_model_info.id,
                )
            )
        ProcessInstanceProcessor.update_spiff_parser_with_all_process_dependency_files(parser)

        try:
            bpmn_process_spec = parser.get_spec(process_model_info.primary_process_id)

            # returns a dict of {process_id: bpmn_process_spec}, otherwise known as an IdToBpmnProcessSpecMapping
            subprocesses = parser.get_subprocess_specs(process_model_info.primary_process_id)
        except ValidationException as ve:
            raise ApiError(
                error_code="process_instance_validation_error",
                message="Failed to parse the Workflow Specification. " + "Error is '%s.'" % str(ve),
                file_name=ve.file_name,
                task_name=ve.name,
                task_id=ve.id,
                tag=ve.tag,
            ) from ve
        return (bpmn_process_spec, subprocesses)

    @staticmethod
    def status_of(bpmn_process_instance: BpmnWorkflow) -> ProcessInstanceStatus:
        if bpmn_process_instance.is_completed():
            return ProcessInstanceStatus.complete
        user_tasks = bpmn_process_instance.get_ready_user_tasks()

        # workflow.waiting_events (includes timers, and timers have a when firing property)

        # if the process instance has status "waiting" it will get picked up
        # by background processing. when that happens it can potentially overwrite
        # human tasks which is bad because we cache them with the previous id's.
        # waiting_tasks = bpmn_process_instance.get_tasks(TaskState.WAITING)
        # waiting_tasks = bpmn_process_instance.get_waiting()
        # if len(waiting_tasks) > 0:
        #     return ProcessInstanceStatus.waiting
        if len(user_tasks) > 0:
            return ProcessInstanceStatus.user_input_required
        else:
            return ProcessInstanceStatus.waiting

    def get_status(self) -> ProcessInstanceStatus:
        the_status = self.status_of(self.bpmn_process_instance)
        # current_app.logger.debug(f"the_status: {the_status} for instance {self.process_instance_model.id}")
        return the_status

    def element_unit_specs_loader(self, process_id: str, element_id: str) -> dict[str, Any] | None:
        full_process_model_hash = self.process_instance_model.bpmn_process_definition.full_process_model_hash
        if full_process_model_hash is None:
            return None

        element_unit_process_dict = ElementUnitsService.workflow_from_cached_element_unit(
            full_process_model_hash,
            process_id,
            element_id,
        )

        if element_unit_process_dict is not None:
            spec_dict = element_unit_process_dict["spec"]
            subprocess_specs_dict = element_unit_process_dict["subprocess_specs"]

            restored_specs = {k: self.wf_spec_converter.restore(v) for k, v in subprocess_specs_dict.items()}
            restored_specs[spec_dict["name"]] = self.wf_spec_converter.restore(spec_dict)

            return restored_specs

        return None

    def lazy_load_subprocess_specs(self) -> None:
        tasks = self.bpmn_process_instance.get_tasks(TaskState.DEFINITE_MASK)
        loaded_specs = set(self.bpmn_process_instance.subprocess_specs.keys())
        for task in tasks:
            if task.task_spec.description != "Call Activity":
                continue
            spec_to_check = task.task_spec.bpmn_id

            if spec_to_check not in loaded_specs:
                lazy_subprocess_specs = self.element_unit_specs_loader(spec_to_check, spec_to_check)
                if lazy_subprocess_specs is None:
                    continue

                for name, spec in lazy_subprocess_specs.items():
                    if name not in loaded_specs:
                        self.bpmn_process_instance.subprocess_specs[name] = spec
                        loaded_specs.add(name)

    def refresh_waiting_tasks(self) -> None:
        self.lazy_load_subprocess_specs()
        self.bpmn_process_instance.refresh_waiting_tasks()

    def do_engine_steps(
        self,
        exit_at: None = None,
        save: bool = False,
        execution_strategy_name: str | None = None,
        execution_strategy: ExecutionStrategy | None = None,
    ) -> None:
        if self.process_instance_model.persistence_level != "none":
            with ProcessInstanceQueueService.dequeued(self.process_instance_model):
                # TODO: ideally we just lock in the execution service, but not sure
                # about _add_bpmn_process_definitions and if that needs to happen in
                # the same lock like it does on main
                self._do_engine_steps(exit_at, save, execution_strategy_name, execution_strategy)
        else:
            self._do_engine_steps(
                exit_at,
                save=False,
                execution_strategy_name=execution_strategy_name,
                execution_strategy=execution_strategy,
            )

    def _do_engine_steps(
        self,
        exit_at: None = None,
        save: bool = False,
        execution_strategy_name: str | None = None,
        execution_strategy: ExecutionStrategy | None = None,
    ) -> None:
        self._add_bpmn_process_definitions()

        task_model_delegate = TaskModelSavingDelegate(
            serializer=self._serializer,
            process_instance=self.process_instance_model,
            bpmn_definition_to_task_definitions_mappings=self.bpmn_definition_to_task_definitions_mappings,
        )

        if execution_strategy is None:
            if execution_strategy_name is None:
                execution_strategy_name = current_app.config["SPIFFWORKFLOW_BACKEND_ENGINE_STEP_DEFAULT_STRATEGY_WEB"]
            if execution_strategy_name is None:
                raise ExecutionStrategyNotConfiguredError(
                    "SPIFFWORKFLOW_BACKEND_ENGINE_STEP_DEFAULT_STRATEGY_WEB has not been set"
                )
            execution_strategy = execution_strategy_named(
                execution_strategy_name, task_model_delegate, self.lazy_load_subprocess_specs
            )

        execution_service = WorkflowExecutionService(
            self.bpmn_process_instance,
            self.process_instance_model,
            execution_strategy,
            self._script_engine.environment.finalize_result,
            self.save,
        )
        execution_service.run_and_save(exit_at, save)

    @classmethod
    def get_tasks_with_data(cls, bpmn_process_instance: BpmnWorkflow) -> list[SpiffTask]:
        return [task for task in bpmn_process_instance.get_tasks(TaskState.FINISHED_MASK) if len(task.data) > 0]

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

    def serialize(self) -> dict:
        self.check_task_data_size()
        self.preserve_script_engine_state()
        return self._serializer.workflow_to_dict(self.bpmn_process_instance)  # type: ignore

    def next_user_tasks(self) -> list[SpiffTask]:
        return self.bpmn_process_instance.get_ready_user_tasks()  # type: ignore

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
            for spiff_task in SpiffTask.Iterator(self.bpmn_process_instance.task_tree, TaskState.ANY_MASK):
                # Assure that we find the end event for this process_instance, and not for any sub-process_instances.
                if TaskService.is_main_process_end_event(spiff_task):
                    endtasks.append(spiff_task)
            if len(endtasks) > 0:
                return endtasks[-1]

        # If there are ready tasks to complete, return the next ready task, but return the one
        # in the active parallel path if possible.  In some cases the active parallel path may itself be
        # a parallel gateway with multiple tasks, so prefer ones that share a parent.

        # Get a list of all ready tasks
        ready_tasks = self.bpmn_process_instance.get_tasks(TaskState.READY)

        if len(ready_tasks) == 0:
            # If no ready tasks exist, check for a waiting task.
            waiting_tasks = self.bpmn_process_instance.get_tasks(TaskState.WAITING)
            if len(waiting_tasks) > 0:
                return waiting_tasks[0]

            # If there are no ready tasks, and not waiting tasks, return the latest error.
            error_task = None
            for task in SpiffTask.Iterator(self.bpmn_process_instance.task_tree, TaskState.ERROR):
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
                if task._is_descendant_of(last_user_task):
                    return task
            for task in ready_tasks:
                if self.bpmn_process_instance.last_task and task.parent == last_user_task.parent:
                    return task

            return ready_tasks[0]

        # If there are no ready tasks, but the thing isn't complete yet, find the first non-complete task
        # and return that
        next_task_to_return = None
        for task in SpiffTask.Iterator(self.bpmn_process_instance.task_tree, TaskState.NOT_FINISHED_MASK):
            next_task_to_return = task
        return next_task_to_return

    def completed_user_tasks(self) -> list[SpiffTask]:
        user_tasks = self.bpmn_process_instance.get_tasks(TaskState.COMPLETED)
        user_tasks.reverse()
        user_tasks = list(
            filter(
                lambda task: task.task_spec.manual,
                user_tasks,
            )
        )
        return user_tasks  # type: ignore

    def get_task_dict_from_spiff_task(self, spiff_task: SpiffTask) -> dict[str, Any]:
        default_registry = DefaultRegistry()
        task_data = default_registry.convert(spiff_task.data)
        python_env = default_registry.convert(self._script_engine.environment.last_result())
        task_json: dict[str, Any] = {
            "task_data": task_data,
            "python_env": python_env,
        }
        return task_json

    def complete_task(self, spiff_task: SpiffTask, human_task: HumanTaskModel, user: UserModel) -> None:
        task_model = TaskModel.query.filter_by(guid=human_task.task_id).first()
        if task_model is None:
            raise TaskNotFoundError(
                f"Cannot find a task with guid {self.process_instance_model.id} and task_id is {human_task.task_id}"
            )

        task_model.start_in_seconds = time.time()
        task_exception = None
        task_event = ProcessInstanceEventType.task_completed.value
        try:
            self.bpmn_process_instance.run_task_from_id(spiff_task.id)
        except Exception as ex:
            task_exception = ex
            task_event = ProcessInstanceEventType.task_failed.value

        task_model.end_in_seconds = time.time()

        human_task.completed_by_user_id = user.id
        human_task.completed = True
        human_task.task_status = spiff_task.get_state_name()
        db.session.add(human_task)

        task_service = TaskService(
            process_instance=self.process_instance_model,
            serializer=self._serializer,
            bpmn_definition_to_task_definitions_mappings=self.bpmn_definition_to_task_definitions_mappings,
        )
        task_service.update_task_model(task_model, spiff_task)
        JsonDataModel.insert_or_update_json_data_records(task_service.json_data_dicts)

        ProcessInstanceTmpService.add_event_to_process_instance(
            self.process_instance_model,
            task_event,
            task_guid=task_model.guid,
            user_id=user.id,
            exception=task_exception,
        )

        # children of a multi-instance task has the attribute "triggered" set to True
        # so use that to determine if a spiff_task is apart of a multi-instance task
        # and therefore we need to process its parent since the current task will not
        # know what is actually going on.
        # Basically "triggered" means "this task is not part of the task spec outputs"
        spiff_task_to_process = spiff_task
        if spiff_task_to_process.triggered is True:
            spiff_task_to_process = spiff_task.parent
        task_service.process_parents_and_children_and_save_to_database(spiff_task_to_process)

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
            elif most_recent_task.last_state_change < task.last_state_change:  # type: ignore
                most_recent_task = task

        if most_recent_task:
            return most_recent_task.data  # type: ignore

        return {}

    def get_process_instance_id(self) -> int:
        return self.process_instance_model.id

    def get_ready_user_tasks(self) -> list[SpiffTask]:
        return self.bpmn_process_instance.get_ready_user_tasks()  # type: ignore

    def get_current_user_tasks(self) -> list[SpiffTask]:
        """Return a list of all user tasks that are READY or COMPLETE and are parallel to the READY Task."""
        ready_tasks = self.bpmn_process_instance.get_ready_user_tasks()
        additional_tasks = []
        if len(ready_tasks) > 0:
            for child in ready_tasks[0].parent.children:
                if child.state == TaskState.COMPLETED:
                    additional_tasks.append(child)
        return ready_tasks + additional_tasks  # type: ignore

    def get_all_user_tasks(self) -> list[SpiffTask]:
        all_tasks = self.bpmn_process_instance.get_tasks(TaskState.ANY_MASK)
        return [t for t in all_tasks if t.task_spec.manual]

    def get_all_completed_tasks(self) -> list[SpiffTask]:
        all_tasks = self.bpmn_process_instance.get_tasks(TaskState.ANY_MASK)
        return [t for t in all_tasks if t.task_spec.manual and t.state in [TaskState.COMPLETED, TaskState.CANCELLED]]

    def get_all_waiting_tasks(self) -> list[SpiffTask]:
        all_tasks = self.bpmn_process_instance.get_tasks(TaskState.ANY_MASK)
        return [t for t in all_tasks if t.state in [TaskState.WAITING]]

    def get_all_ready_or_waiting_tasks(self) -> list[SpiffTask]:
        all_tasks = self.bpmn_process_instance.get_tasks(TaskState.ANY_MASK)
        return [t for t in all_tasks if t.state in [TaskState.WAITING, TaskState.READY]]

    def get_task_by_guid(self, task_guid: str) -> SpiffTask | None:
        return self.bpmn_process_instance.get_task_from_id(UUID(task_guid))

    @classmethod
    def get_task_by_bpmn_identifier(
        cls, bpmn_task_identifier: str, bpmn_process_instance: BpmnWorkflow
    ) -> SpiffTask | None:
        all_tasks = bpmn_process_instance.get_tasks(TaskState.ANY_MASK)
        for task in all_tasks:
            if task.task_spec.name == bpmn_task_identifier:
                return task
        return None

    def remove_spiff_tasks_for_termination(self) -> None:
        start_time = time.time()
        deleted_tasks = self.bpmn_process_instance.cancel() or []
        spiff_tasks = self.bpmn_process_instance.get_tasks()

        task_service = TaskService(
            process_instance=self.process_instance_model,
            serializer=self._serializer,
            bpmn_definition_to_task_definitions_mappings=self.bpmn_definition_to_task_definitions_mappings,
        )
        task_service.update_all_tasks_from_spiff_tasks(spiff_tasks, deleted_tasks, start_time)

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

    def resume(self) -> None:
        self.process_instance_model.status = ProcessInstanceStatus.waiting.value
        db.session.add(self.process_instance_model)
        ProcessInstanceTmpService.add_event_to_process_instance(
            self.process_instance_model, ProcessInstanceEventType.process_instance_resumed.value
        )
        db.session.commit()
