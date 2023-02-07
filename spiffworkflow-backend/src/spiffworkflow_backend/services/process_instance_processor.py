"""Process_instance_processor."""
import _strptime  # type: ignore
import decimal
import json
import logging
import os
import re
import time
from datetime import datetime
from datetime import timedelta
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import NewType
from typing import Optional
from typing import Tuple
from typing import TypedDict
from typing import Union
from uuid import UUID

import dateparser
import pytz
from flask import current_app
from lxml import etree  # type: ignore
from lxml.etree import XMLSyntaxError  # type: ignore
from RestrictedPython import safe_globals  # type: ignore
from SpiffWorkflow.bpmn.parser.ValidationException import ValidationException  # type: ignore
from SpiffWorkflow.bpmn.PythonScriptEngine import PythonScriptEngine  # type: ignore
from SpiffWorkflow.bpmn.PythonScriptEngineEnvironment import BasePythonScriptEngineEnvironment  # type: ignore
from SpiffWorkflow.bpmn.PythonScriptEngineEnvironment import Box
from SpiffWorkflow.bpmn.PythonScriptEngineEnvironment import BoxedTaskDataEnvironment
from SpiffWorkflow.bpmn.serializer.task_spec import (  # type: ignore
    EventBasedGatewayConverter,
)
from SpiffWorkflow.bpmn.serializer.workflow import BpmnWorkflowSerializer  # type: ignore
from SpiffWorkflow.bpmn.specs.BpmnProcessSpec import BpmnProcessSpec  # type: ignore
from SpiffWorkflow.bpmn.specs.events.EndEvent import EndEvent  # type: ignore
from SpiffWorkflow.bpmn.specs.events.event_definitions import CancelEventDefinition  # type: ignore
from SpiffWorkflow.bpmn.specs.events.StartEvent import StartEvent  # type: ignore
from SpiffWorkflow.bpmn.specs.SubWorkflowTask import SubWorkflowTask  # type: ignore
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow  # type: ignore
from SpiffWorkflow.dmn.parser.BpmnDmnParser import BpmnDmnParser  # type: ignore
from SpiffWorkflow.dmn.serializer.task_spec import BusinessRuleTaskConverter  # type: ignore
from SpiffWorkflow.exceptions import SpiffWorkflowException  # type: ignore
from SpiffWorkflow.exceptions import WorkflowException
from SpiffWorkflow.exceptions import WorkflowTaskException
from SpiffWorkflow.serializer.exceptions import MissingSpecError  # type: ignore
from SpiffWorkflow.spiff.serializer.config import SPIFF_SPEC_CONFIG  # type: ignore
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore
from SpiffWorkflow.task import TaskState
from SpiffWorkflow.util.deep_merge import DeepMerge  # type: ignore
from sqlalchemy import text

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.file import File
from spiffworkflow_backend.models.file import FileType
from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.human_task_user import HumanTaskUserModel
from spiffworkflow_backend.models.message_correlation import MessageCorrelationModel
from spiffworkflow_backend.models.message_correlation_message_instance import (
    MessageCorrelationMessageInstanceModel,
)
from spiffworkflow_backend.models.message_correlation_property import (
    MessageCorrelationPropertyModel,
)
from spiffworkflow_backend.models.message_instance import MessageInstanceModel
from spiffworkflow_backend.models.message_instance import MessageModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
from spiffworkflow_backend.models.process_instance_metadata import (
    ProcessInstanceMetadataModel,
)
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.models.script_attributes_context import (
    ScriptAttributesContext,
)
from spiffworkflow_backend.models.spec_reference import SpecReferenceCache
from spiffworkflow_backend.models.spiff_step_details import SpiffStepDetailsModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.models.user import UserModelSchema
from spiffworkflow_backend.scripts.script import Script
from spiffworkflow_backend.services.custom_parser import MyCustomParser
from spiffworkflow_backend.services.file_system_service import FileSystemService
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.service_task_service import ServiceTaskDelegate
from spiffworkflow_backend.services.spec_file_service import SpecFileService
from spiffworkflow_backend.services.user_service import UserService

SPIFF_SPEC_CONFIG["task_specs"].append(BusinessRuleTaskConverter)


# Sorry about all this crap.  I wanted to move this thing to another file, but
# importing a bunch of types causes circular imports.


def _import(name: str, glbls: Dict[str, Any], *args: Any) -> None:
    """_import."""
    if name not in glbls:
        raise ImportError(f"Import not allowed: {name}", name=name)


class PotentialOwnerIdList(TypedDict):
    """PotentialOwnerIdList."""

    potential_owner_ids: list[int]
    lane_assignment_id: Optional[int]


class ProcessInstanceProcessorError(Exception):
    """ProcessInstanceProcessorError."""


class NoPotentialOwnersForTaskError(Exception):
    """NoPotentialOwnersForTaskError."""


class PotentialOwnerUserNotFoundError(Exception):
    """PotentialOwnerUserNotFoundError."""


class MissingProcessInfoError(Exception):
    """MissingProcessInfoError."""


class ProcessInstanceIsAlreadyLockedError(Exception):
    pass


class ProcessInstanceLockedBySomethingElseError(Exception):
    pass


class BoxedTaskDataBasedScriptEngineEnvironment(BoxedTaskDataEnvironment):  # type: ignore
    def __init__(self, environment_globals: Dict[str, Any]):
        """BoxedTaskDataBasedScriptEngineEnvironment."""
        self._last_result: Dict[str, Any] = {}
        super().__init__(environment_globals)

    def execute(
        self,
        script: str,
        context: Dict[str, Any],
        external_methods: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().execute(script, context, external_methods)
        self._last_result = context

    def last_result(self) -> Dict[str, Any]:
        return {k: v for k, v in self._last_result.items()}

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

    def __init__(self, environment_globals: Dict[str, Any]):
        """NonTaskDataBasedScriptEngineEnvironment."""
        self.state: Dict[str, Any] = {}
        self.non_user_defined_keys = set(
            [*environment_globals.keys()] + ["__builtins__", "current_user"]
        )
        super().__init__(environment_globals)

    def evaluate(
        self,
        expression: str,
        context: Dict[str, Any],
        external_methods: Optional[dict[str, Any]] = None,
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
        context: Dict[str, Any],
        external_methods: Optional[Dict[str, Any]] = None,
    ) -> None:
        # TODO: once integrated look at the tests that fail without Box
        Box.convert_to_box(context)
        self.state.update(self.globals)
        self.state.update(external_methods or {})
        self.state.update(context)
        exec(script, self.state)  # noqa

        self.state = self._user_defined_state(external_methods)

        # the task data needs to be updated with the current state so data references can be resolved properly.
        # the state will be removed later once the task is completed.
        context.update(self.state)

    def _user_defined_state(
        self, external_methods: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        keys_to_filter = self.non_user_defined_keys
        if external_methods is not None:
            keys_to_filter |= set(external_methods.keys())

        return {
            k: v
            for k, v in self.state.items()
            if k not in keys_to_filter and not callable(v)
        }

    def last_result(self) -> Dict[str, Any]:
        return {k: v for k, v in self.state.items()}

    def clear_state(self) -> None:
        self.state = {}

    def preserve_state(self, bpmn_process_instance: BpmnWorkflow) -> None:
        key = self.PYTHON_ENVIRONMENT_STATE_KEY
        state = self._user_defined_state()
        bpmn_process_instance.data[key] = state

    def restore_state(self, bpmn_process_instance: BpmnWorkflow) -> None:
        key = self.PYTHON_ENVIRONMENT_STATE_KEY
        self.state = bpmn_process_instance.data.get(key, {})

    def finalize_result(self, bpmn_process_instance: BpmnWorkflow) -> None:
        bpmn_process_instance.data.update(self._user_defined_state())

    def revise_state_with_task_data(self, task: SpiffTask) -> None:
        state_keys = set(self.state.keys())
        task_data_keys = set(task.data.keys())
        state_keys_to_remove = state_keys - task_data_keys
        task_data_keys_to_keep = task_data_keys - state_keys

        self.state = {
            k: v for k, v in self.state.items() if k not in state_keys_to_remove
        }
        task.data = {k: v for k, v in task.data.items() if k in task_data_keys_to_keep}

        if hasattr(task.task_spec, "_result_variable"):
            result_variable = task.task_spec._result_variable(task)
            if result_variable in task.data:
                self.state[result_variable] = task.data.pop(result_variable)


class CustomScriptEngineEnvironment(NonTaskDataBasedScriptEngineEnvironment):
    pass


class CustomBpmnScriptEngine(PythonScriptEngine):  # type: ignore
    """This is a custom script processor that can be easily injected into Spiff Workflow.

    It will execute python code read in from the bpmn.  It will also make any scripts in the
    scripts directory available for execution.
    """

    def __init__(self) -> None:
        """__init__."""
        default_globals = {
            "_strptime": _strptime,
            "dateparser": dateparser,
            "datetime": datetime,
            "decimal": decimal,
            "enumerate": enumerate,
            "format": format,
            "list": list,
            "map": map,
            "pytz": pytz,
            "sum": sum,
            "time": time,
            "timedelta": timedelta,
            "set": set,
        }

        # This will overwrite the standard builtins
        default_globals.update(safe_globals)
        default_globals["__builtins__"]["__import__"] = _import

        environment = CustomScriptEngineEnvironment(default_globals)

        super().__init__(environment=environment)

    def __get_augment_methods(self, task: SpiffTask) -> Dict[str, Callable]:
        """__get_augment_methods."""
        tld = current_app.config["THREAD_LOCAL_DATA"]

        if not hasattr(tld, "process_model_identifier"):
            raise MissingProcessInfoError(
                "Could not find process_model_identifier from app config"
            )
        if not hasattr(tld, "process_instance_id"):
            raise MissingProcessInfoError(
                "Could not find process_instance_id from app config"
            )

        process_model_identifier = tld.process_model_identifier
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
        external_methods: Optional[dict[str, Any]] = None,
    ) -> Any:
        """Evaluate."""
        return self._evaluate(expression, task.data, task, external_methods)

    def _evaluate(
        self,
        expression: str,
        context: Dict[str, Union[Box, str]],
        task: Optional[SpiffTask] = None,
        external_methods: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """_evaluate."""
        methods = self.__get_augment_methods(task)
        if external_methods:
            methods.update(external_methods)

        """Evaluate the given expression, within the context of the given task and return the result."""
        try:
            return super()._evaluate(expression, context, external_methods=methods)
        except Exception as exception:
            if task is None:
                raise WorkflowException(
                    "Error evaluating expression: '%s', %s"
                    % (expression, str(exception)),
                ) from exception
            else:
                raise WorkflowTaskException(
                    "Error evaluating expression '%s', %s"
                    % (expression, str(exception)),
                    task=task,
                    exception=exception,
                ) from exception

    def execute(
        self, task: SpiffTask, script: str, external_methods: Any = None
    ) -> None:
        """Execute."""
        try:
            methods = self.__get_augment_methods(task)
            if external_methods:
                methods.update(external_methods)
            super().execute(task, script, methods)
        except WorkflowException as e:
            raise e
        except Exception as e:
            raise self.create_task_exec_exception(task, script, e) from e

    def call_service(
        self,
        operation_name: str,
        operation_params: Dict[str, Any],
        task_data: Dict[str, Any],
    ) -> Any:
        """CallService."""
        return ServiceTaskDelegate.call_connector(
            operation_name, operation_params, task_data
        )


IdToBpmnProcessSpecMapping = NewType(
    "IdToBpmnProcessSpecMapping", dict[str, BpmnProcessSpec]
)


class ProcessInstanceProcessor:
    """ProcessInstanceProcessor."""

    _script_engine = CustomBpmnScriptEngine()
    SERIALIZER_VERSION = "1.0-spiffworkflow-backend"

    wf_spec_converter = BpmnWorkflowSerializer.configure_workflow_spec_converter(
        SPIFF_SPEC_CONFIG
    )
    _serializer = BpmnWorkflowSerializer(wf_spec_converter, version=SERIALIZER_VERSION)
    _event_serializer = EventBasedGatewayConverter(wf_spec_converter)

    PROCESS_INSTANCE_ID_KEY = "process_instance_id"
    VALIDATION_PROCESS_KEY = "validate_only"

    # __init__ calls these helpers:
    #   * get_spec, which returns a spec and any subprocesses (as IdToBpmnProcessSpecMapping dict)
    #   * __get_bpmn_process_instance, which takes spec and subprocesses and instantiates and returns a BpmnWorkflow
    def __init__(
        self, process_instance_model: ProcessInstanceModel, validate_only: bool = False
    ) -> None:
        """Create a Workflow Processor based on the serialized information available in the process_instance model."""
        tld = current_app.config["THREAD_LOCAL_DATA"]
        tld.process_instance_id = process_instance_model.id
        tld.spiff_step = process_instance_model.spiff_step

        # we want this to be the fully qualified path to the process model including all group subcomponents
        current_app.config["THREAD_LOCAL_DATA"].process_model_identifier = (
            f"{process_instance_model.process_model_identifier}"
        )

        self.process_instance_model = process_instance_model
        self.process_model_service = ProcessModelService()
        bpmn_process_spec = None
        subprocesses: Optional[IdToBpmnProcessSpecMapping] = None
        if process_instance_model.bpmn_json is None:
            (
                bpmn_process_spec,
                subprocesses,
            ) = ProcessInstanceProcessor.get_process_model_and_subprocesses(
                process_instance_model.process_model_identifier
            )
        else:
            bpmn_json_length = len(process_instance_model.bpmn_json.encode("utf-8"))
            megabyte = float(1024**2)
            json_size = bpmn_json_length / megabyte
            if json_size > 1:
                wf_json = json.loads(process_instance_model.bpmn_json)
                if "spec" in wf_json and "tasks" in wf_json:
                    task_tree = wf_json["tasks"]
                    test_spec = wf_json["spec"]
                    task_size = "{:.2f}".format(
                        len(json.dumps(task_tree).encode("utf-8")) / megabyte
                    )
                    spec_size = "{:.2f}".format(
                        len(json.dumps(test_spec).encode("utf-8")) / megabyte
                    )
                    message = (
                        "Workflow "
                        + process_instance_model.process_model_identifier
                        + f" JSON Size is over 1MB:{json_size:.2f} MB"
                    )
                    message += f"\n  Task Size: {task_size}"
                    message += f"\n  Spec Size: {spec_size}"
                    current_app.logger.warning(message)

                    def check_sub_specs(
                        test_spec: dict, indent: int = 0, show_all: bool = False
                    ) -> None:
                        """Check_sub_specs."""
                        for my_spec_name in test_spec["task_specs"]:
                            my_spec = test_spec["task_specs"][my_spec_name]
                            my_spec_size = (
                                len(json.dumps(my_spec).encode("utf-8")) / megabyte
                            )
                            if my_spec_size > 0.1 or show_all:
                                current_app.logger.warning(
                                    (" " * indent)
                                    + "Sub-Spec "
                                    + my_spec["name"]
                                    + " :"
                                    + f"{my_spec_size:.2f}"
                                )
                                if "spec" in my_spec:
                                    if my_spec["name"] == "Call_Emails_Process_Email":
                                        pass
                                    check_sub_specs(my_spec["spec"], indent + 5)

                    check_sub_specs(test_spec, 5)

        self.process_model_identifier = process_instance_model.process_model_identifier
        self.process_model_display_name = (
            process_instance_model.process_model_display_name
        )

        try:
            self.bpmn_process_instance = self.__get_bpmn_process_instance(
                process_instance_model,
                bpmn_process_spec,
                validate_only,
                subprocesses=subprocesses,
            )
            self.set_script_engine(self.bpmn_process_instance)
            self.add_user_info_to_process_instance(self.bpmn_process_instance)

        except MissingSpecError as ke:
            raise ApiError(
                error_code="unexpected_process_instance_structure",
                message=(
                    "Failed to deserialize process_instance"
                    " '%s'  due to a mis-placed or missing task '%s'"
                )
                % (self.process_model_identifier, str(ke)),
            ) from ke

    @classmethod
    def get_process_model_and_subprocesses(
        cls, process_model_identifier: str
    ) -> Tuple[BpmnProcessSpec, IdToBpmnProcessSpecMapping]:
        """Get_process_model_and_subprocesses."""
        process_model_info = ProcessModelService.get_process_model(
            process_model_identifier
        )
        if process_model_info is None:
            raise (
                ApiError(
                    "process_model_not_found",
                    (
                        "The given process model was not found:"
                        f" {process_model_identifier}."
                    ),
                )
            )
        spec_files = SpecFileService.get_files(process_model_info)
        return cls.get_spec(spec_files, process_model_info)

    @classmethod
    def get_bpmn_process_instance_from_process_model(
        cls, process_model_identifier: str
    ) -> BpmnWorkflow:
        """Get_all_bpmn_process_identifiers_for_process_model."""
        (bpmn_process_spec, subprocesses) = cls.get_process_model_and_subprocesses(
            process_model_identifier,
        )
        return cls.get_bpmn_process_instance_from_workflow_spec(
            bpmn_process_spec, subprocesses
        )

    @staticmethod
    def set_script_engine(bpmn_process_instance: BpmnWorkflow) -> None:
        ProcessInstanceProcessor._script_engine.environment.restore_state(
            bpmn_process_instance
        )
        bpmn_process_instance.script_engine = ProcessInstanceProcessor._script_engine

    def preserve_script_engine_state(self) -> None:
        ProcessInstanceProcessor._script_engine.environment.preserve_state(
            self.bpmn_process_instance
        )

    def current_user(self) -> Any:
        """Current_user."""
        current_user = None
        if UserService.has_user():
            current_user = UserService.current_user()

        # fall back to initiator if g.user is not set
        # this is for background processes when there will not be a user
        #   coming in from the api
        elif self.process_instance_model.process_initiator_id:
            current_user = self.process_instance_model.process_initiator

        return current_user

    def add_user_info_to_process_instance(
        self, bpmn_process_instance: BpmnWorkflow
    ) -> None:
        """Add_user_info_to_process_instance."""
        current_user = self.current_user()

        if current_user:
            current_user_data = UserModelSchema().dump(current_user)
            tasks = bpmn_process_instance.get_tasks(TaskState.READY)
            for task in tasks:
                task.data["current_user"] = current_user_data

    @staticmethod
    def get_bpmn_process_instance_from_workflow_spec(
        spec: BpmnProcessSpec,
        subprocesses: Optional[IdToBpmnProcessSpecMapping] = None,
    ) -> BpmnWorkflow:
        """Get_bpmn_process_instance_from_workflow_spec."""
        bpmn_process_instance = BpmnWorkflow(
            spec,
            subprocess_specs=subprocesses,
        )
        ProcessInstanceProcessor.set_script_engine(bpmn_process_instance)
        return bpmn_process_instance

    @staticmethod
    def __get_bpmn_process_instance(
        process_instance_model: ProcessInstanceModel,
        spec: Optional[BpmnProcessSpec] = None,
        validate_only: bool = False,
        subprocesses: Optional[IdToBpmnProcessSpecMapping] = None,
    ) -> BpmnWorkflow:
        """__get_bpmn_process_instance."""
        if process_instance_model.bpmn_json:
            # turn off logging to avoid duplicated spiff logs
            spiff_logger = logging.getLogger("spiff")
            original_spiff_logger_log_level = spiff_logger.level
            spiff_logger.setLevel(logging.WARNING)

            try:
                bpmn_process_instance = (
                    ProcessInstanceProcessor._serializer.deserialize_json(
                        process_instance_model.bpmn_json
                    )
                )
            except Exception as err:
                raise err
            finally:
                spiff_logger.setLevel(original_spiff_logger_log_level)

            ProcessInstanceProcessor.set_script_engine(bpmn_process_instance)
        else:
            bpmn_process_instance = (
                ProcessInstanceProcessor.get_bpmn_process_instance_from_workflow_spec(
                    spec, subprocesses
                )
            )
            bpmn_process_instance.data[
                ProcessInstanceProcessor.VALIDATION_PROCESS_KEY
            ] = validate_only
        return bpmn_process_instance

    def slam_in_data(self, data: dict) -> None:
        """Slam_in_data."""
        self.bpmn_process_instance.data = DeepMerge.merge(
            self.bpmn_process_instance.data, data
        )

        self.save()

    def raise_if_no_potential_owners(
        self, potential_owner_ids: list[int], message: str
    ) -> None:
        """Raise_if_no_potential_owners."""
        if not potential_owner_ids:
            raise NoPotentialOwnersForTaskError(message)

    def get_potential_owner_ids_from_task(
        self, task: SpiffTask
    ) -> PotentialOwnerIdList:
        """Get_potential_owner_ids_from_task."""
        task_spec = task.task_spec
        task_lane = "process_initiator"
        if task_spec.lane is not None and task_spec.lane != "":
            task_lane = task_spec.lane

        potential_owner_ids = []
        lane_assignment_id = None
        if re.match(r"(process.?)initiator", task_lane, re.IGNORECASE):
            potential_owner_ids = [self.process_instance_model.process_initiator_id]
        elif "lane_owners" in task.data and task_lane in task.data["lane_owners"]:
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
            group_model = GroupModel.query.filter_by(identifier=task_lane).first()
            if group_model is None:
                raise (
                    NoPotentialOwnersForTaskError(
                        f"Could not find a group with name matching lane: {task_lane}"
                    )
                )
            potential_owner_ids = [
                i.user_id for i in group_model.user_group_assignments
            ]
            lane_assignment_id = group_model.id
            self.raise_if_no_potential_owners(
                potential_owner_ids,
                f"Could not find any users in group to assign to lane: {task_lane}",
            )

        return {
            "potential_owner_ids": potential_owner_ids,
            "lane_assignment_id": lane_assignment_id,
        }

    def spiff_step_details_mapping(self) -> dict:
        """SaveSpiffStepDetails."""
        # bpmn_json = self.serialize()
        # wf_json = json.loads(bpmn_json)
        task_json: Dict[str, Any] = {
            # "tasks": wf_json["tasks"],
            # "subprocesses": wf_json["subprocesses"],
            # "python_env": self._script_engine.environment.last_result(),
        }

        return {
            "process_instance_id": self.process_instance_model.id,
            "spiff_step": self.process_instance_model.spiff_step or 1,
            "task_json": task_json,
            "timestamp": round(time.time()),
            # "completed_by_user_id": self.current_user().id,
        }

    def spiff_step_details(self) -> SpiffStepDetailsModel:
        """SaveSpiffStepDetails."""
        details_mapping = self.spiff_step_details_mapping()
        details_model = SpiffStepDetailsModel(**details_mapping)
        return details_model

    def extract_metadata(self, process_model_info: ProcessModelInfo) -> None:
        """Extract_metadata."""
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
                pim.value = data_for_key
                db.session.add(pim)
                db.session.commit()

    # FIXME: Better to move to SpiffWorkflow and traverse the outer_workflows on the spiff_task
    # We may need to add whether a subprocess is a call activity or a subprocess in order to do it properly
    def get_all_processes_with_task_name_list(self) -> dict[str, list[str]]:
        """Gets the list of processes pointing to a list of task names.

        This is useful for figuring out which process contain which task.

        Rerturns: {process_name: [task_1, task_2, ...], ...}
        """
        serialized_data = json.loads(self.serialize())
        processes: dict[str, list[str]] = {serialized_data["spec"]["name"]: []}
        for task_name, _task_spec in serialized_data["spec"]["task_specs"].items():
            processes[serialized_data["spec"]["name"]].append(task_name)
        if "subprocess_specs" in serialized_data:
            for subprocess_name, subprocess_details in serialized_data[
                "subprocess_specs"
            ].items():
                processes[subprocess_name] = []
                if "task_specs" in subprocess_details:
                    for task_name, _task_spec in subprocess_details[
                        "task_specs"
                    ].items():
                        processes[subprocess_name].append(task_name)
        return processes

    def find_process_model_process_name_by_task_name(
        self, task_name: str, processes: Optional[dict[str, list[str]]] = None
    ) -> str:
        """Gets the top level process of a process model using the task name that the process contains.

        For example, process_modelA has processA which has a call activity that calls processB which is inside of process_modelB.
        processB has subprocessA which has taskA. Using taskA this method should return processB and then that can be used with
        the spec reference cache to find process_modelB.
        """
        process_name_to_return = task_name
        if processes is None:
            processes = self.get_all_processes_with_task_name_list()

        for process_name, task_spec_names in processes.items():
            if task_name in task_spec_names:
                process_name_to_return = (
                    self.find_process_model_process_name_by_task_name(
                        process_name, processes
                    )
                )
        return process_name_to_return

    #################################################################

    def get_all_task_specs(self) -> dict[str, dict]:
        """This looks both at top level task_specs and subprocess_specs in the serialized data.

        It returns a dict of all task specs based on the task name like it is in the serialized form.

        NOTE: this may not fully work for tasks that are NOT call activities since their task_name may not be unique
        but in our current use case we only care about the call activities here.
        """
        serialized_data = json.loads(self.serialize())
        spiff_task_json = serialized_data["spec"]["task_specs"] or {}
        if "subprocess_specs" in serialized_data:
            for _subprocess_name, subprocess_details in serialized_data[
                "subprocess_specs"
            ].items():
                if "task_specs" in subprocess_details:
                    spiff_task_json = spiff_task_json | subprocess_details["task_specs"]
        return spiff_task_json

    def get_subprocesses_by_child_task_ids(self) -> Tuple[dict, dict]:
        """Get all subprocess ids based on the child task ids.

        This is useful when trying to link the child task of a call activity back to
        the call activity that called it to get the appropriate data. For example, if you
        have a call activity "Log" that you call twice within the same process, the Hammer log file
        activity within the Log process will get called twice. They will potentially have different
        task data. We want to be able to differentiate those two activities.

        subprocess structure in the json:
            "subprocesses": { [subprocess_task_id]: "tasks" : { [task_id]: [bpmn_task_details] }}

        Also note that subprocess_task_id might in fact be a call activity, because spiff treats
        call activities like subprocesses in terms of the serialization.
        """
        bpmn_json = json.loads(self.serialize())
        spiff_task_json = self.get_all_task_specs()

        subprocesses_by_child_task_ids = {}
        task_typename_by_task_id = {}
        if "subprocesses" in bpmn_json:
            for subprocess_id, subprocess_details in bpmn_json["subprocesses"].items():
                for task_id, task_details in subprocess_details["tasks"].items():
                    subprocesses_by_child_task_ids[task_id] = subprocess_id
                    task_name = task_details["task_spec"]
                    if task_name in spiff_task_json:
                        task_typename_by_task_id[task_id] = spiff_task_json[task_name][
                            "typename"
                        ]
        return (subprocesses_by_child_task_ids, task_typename_by_task_id)

    def get_highest_level_calling_subprocesses_by_child_task_ids(
        self, subprocesses_by_child_task_ids: dict, task_typename_by_task_id: dict
    ) -> dict:
        """Ensure task ids point to the top level subprocess id.

        This is done by checking if a subprocess is also a task until the subprocess is no longer a task or a Call Activity.
        """
        for task_id, subprocess_id in subprocesses_by_child_task_ids.items():
            if subprocess_id in subprocesses_by_child_task_ids:
                current_subprocess_id_for_task = subprocesses_by_child_task_ids[task_id]
                if current_subprocess_id_for_task in task_typename_by_task_id:
                    # a call activity is like the top-level subprocess since it is the calling subprocess
                    # according to spiff and the top-level calling subprocess is really what we care about
                    if (
                        task_typename_by_task_id[current_subprocess_id_for_task]
                        == "CallActivity"
                    ):
                        continue

                subprocesses_by_child_task_ids[task_id] = (
                    subprocesses_by_child_task_ids[subprocess_id]
                )
                self.get_highest_level_calling_subprocesses_by_child_task_ids(
                    subprocesses_by_child_task_ids, task_typename_by_task_id
                )
        return subprocesses_by_child_task_ids

    def save(self) -> None:
        """Saves the current state of this processor to the database."""
        self.process_instance_model.bpmn_json = self.serialize()

        complete_states = [TaskState.CANCELLED, TaskState.COMPLETED]
        user_tasks = list(self.get_all_user_tasks())
        self.process_instance_model.status = self.get_status().value
        current_app.logger.debug(
            f"the_status: {self.process_instance_model.status} for instance"
            f" {self.process_instance_model.id}"
        )
        self.process_instance_model.total_tasks = len(user_tasks)
        self.process_instance_model.completed_tasks = sum(
            1 for t in user_tasks if t.state in complete_states
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
        process_model_info = self.process_model_service.get_process_model(
            self.process_instance_model.process_model_identifier
        )
        if process_model_info is not None:
            process_model_display_name = process_model_info.display_name

        self.extract_metadata(process_model_info)

        for ready_or_waiting_task in ready_or_waiting_tasks:
            # filter out non-usertasks
            task_spec = ready_or_waiting_task.task_spec
            if not self.bpmn_process_instance._is_engine_task(task_spec):
                potential_owner_hash = self.get_potential_owner_ids_from_task(
                    ready_or_waiting_task
                )
                extensions = ready_or_waiting_task.task_spec.extensions

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
                    human_task = HumanTaskModel(
                        process_instance_id=self.process_instance_model.id,
                        process_model_display_name=process_model_display_name,
                        form_file_name=form_file_name,
                        ui_form_file_name=ui_form_file_name,
                        task_id=str(ready_or_waiting_task.id),
                        task_name=ready_or_waiting_task.task_spec.name,
                        task_title=ready_or_waiting_task.task_spec.description,
                        task_type=ready_or_waiting_task.task_spec.__class__.__name__,
                        task_status=ready_or_waiting_task.get_state_name(),
                        lane_assignment_id=potential_owner_hash["lane_assignment_id"],
                    )
                    db.session.add(human_task)
                    db.session.commit()

                    for potential_owner_id in potential_owner_hash[
                        "potential_owner_ids"
                    ]:
                        human_task_user = HumanTaskUserModel(
                            user_id=potential_owner_id, human_task_id=human_task.id
                        )
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
        if payload is not None:
            event_definition.payload = payload
        current_app.logger.info(
            f"Event of type {event_definition.event_type} sent to process instance"
            f" {self.process_instance_model.id}"
        )
        try:
            self.bpmn_process_instance.catch(event_definition)
        except Exception as e:
            print(e)
        self.do_engine_steps(save=True)

    def add_step(self, step: Union[dict, None] = None) -> None:
        """Add a spiff step."""
        if step is None:
            step = self.spiff_step_details_mapping()
        db.session.add(SpiffStepDetailsModel(**step))
        db.session.commit()

    def manual_complete_task(self, task_id: str, execute: bool) -> None:
        """Mark the task complete optionally executing it."""
        spiff_task = self.bpmn_process_instance.get_task(UUID(task_id))
        if execute:
            current_app.logger.info(
                f"Manually executing Task {spiff_task.task_spec.name} of process"
                f" instance {self.process_instance_model.id}"
            )
            # Executing a subworkflow manually will restart its subprocess and allow stepping through it
            if isinstance(spiff_task.task_spec, SubWorkflowTask):
                subprocess = self.bpmn_process_instance.get_subprocess(spiff_task)
                # We have to get to the actual start event
                for task in self.bpmn_process_instance.get_tasks(workflow=subprocess):
                    task.complete()
                    if isinstance(task.task_spec, StartEvent):
                        break
            else:
                spiff_task.complete()
        else:
            spiff_logger = logging.getLogger("spiff")
            spiff_logger.info(
                f"Skipped task {spiff_task.task_spec.name}", extra=spiff_task.log_info()
            )
            spiff_task._set_state(TaskState.COMPLETED)
            for child in spiff_task.children:
                child.task_spec._update(child)
            spiff_task.workflow.last_task = spiff_task

        if isinstance(spiff_task.task_spec, EndEvent):
            for task in self.bpmn_process_instance.get_tasks(
                TaskState.DEFINITE_MASK, workflow=spiff_task.workflow
            ):
                task.complete()

        # A subworkflow task will become ready when its workflow is complete.  Engine steps would normally
        # then complete it, but we have to do it ourselves here.
        for task in self.bpmn_process_instance.get_tasks(TaskState.READY):
            if isinstance(task.task_spec, SubWorkflowTask):
                task.complete()

        self.increment_spiff_step()
        self.add_step()
        self.save()
        # Saving the workflow seems to reset the status
        self.suspend()

    def reset_process(self, spiff_step: int) -> None:
        """Reset a process to an earlier state."""
        spiff_logger = logging.getLogger("spiff")
        spiff_logger.info(
            f"Process reset from step {spiff_step}",
            extra=self.bpmn_process_instance.log_info(),
        )

        step_detail = (
            db.session.query(SpiffStepDetailsModel)
            .filter(
                SpiffStepDetailsModel.process_instance_id
                == self.process_instance_model.id,
                SpiffStepDetailsModel.spiff_step == spiff_step,
            )
            .first()
        )
        if step_detail is not None:
            self.increment_spiff_step()
            self.add_step(
                {
                    "process_instance_id": self.process_instance_model.id,
                    "spiff_step": self.process_instance_model.spiff_step or 1,
                    "task_json": step_detail.task_json,
                    "timestamp": round(time.time()),
                }
            )

            dct = self._serializer.workflow_to_dict(self.bpmn_process_instance)
            dct["tasks"] = step_detail.task_json["tasks"]
            dct["subprocesses"] = step_detail.task_json["subprocesses"]
            self.bpmn_process_instance = self._serializer.workflow_from_dict(dct)

            # Cascade does not seems to work on filters, only directly through the session
            tasks = self.bpmn_process_instance.get_tasks(TaskState.NOT_FINISHED_MASK)
            rows = HumanTaskModel.query.filter(
                HumanTaskModel.task_id.in_(str(t.id) for t in tasks)  # type: ignore
            ).all()
            for row in rows:
                db.session.delete(row)

            self.save()
            self.suspend()

    @staticmethod
    def get_parser() -> MyCustomParser:
        """Get_parser."""
        parser = MyCustomParser()
        return parser

    @staticmethod
    def backfill_missing_spec_reference_records(
        bpmn_process_identifier: str,
    ) -> Optional[str]:
        """Backfill_missing_spec_reference_records."""
        process_models = ProcessModelService.get_process_models(recursive=True)
        for process_model in process_models:
            try:
                refs = SpecFileService.reference_map(
                    SpecFileService.get_references_for_process(process_model)
                )
                bpmn_process_identifiers = refs.keys()
                if bpmn_process_identifier in bpmn_process_identifiers:
                    SpecFileService.update_process_cache(refs[bpmn_process_identifier])
                    return FileSystemService.full_path_to_process_model_file(
                        process_model
                    )
            except Exception:
                current_app.logger.warning("Failed to parse process ", process_model.id)
        return None

    @staticmethod
    def bpmn_file_full_path_from_bpmn_process_identifier(
        bpmn_process_identifier: str,
    ) -> str:
        """Bpmn_file_full_path_from_bpmn_process_identifier."""
        if bpmn_process_identifier is None:
            raise ValueError(
                "bpmn_file_full_path_from_bpmn_process_identifier:"
                " bpmn_process_identifier is unexpectedly None"
            )

        spec_reference = SpecReferenceCache.query.filter_by(
            identifier=bpmn_process_identifier, type="process"
        ).first()
        bpmn_file_full_path = None
        if spec_reference is None:
            bpmn_file_full_path = (
                ProcessInstanceProcessor.backfill_missing_spec_reference_records(
                    bpmn_process_identifier
                )
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
                    message=(
                        "Could not find the the given bpmn process identifier from any"
                        " sources: %s"
                    )
                    % bpmn_process_identifier,
                )
            )
        return os.path.abspath(bpmn_file_full_path)

    @staticmethod
    def update_spiff_parser_with_all_process_dependency_files(
        parser: BpmnDmnParser,
        processed_identifiers: Optional[set[str]] = None,
    ) -> None:
        """Update_spiff_parser_with_all_process_dependency_files."""
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
            dmn_file_glob = os.path.join(
                os.path.dirname(new_bpmn_file_full_path), "*.dmn"
            )
            parser.add_dmn_files_by_glob(dmn_file_glob)
            processed_identifiers.add(bpmn_process_identifier)

        if new_bpmn_files:
            parser.add_bpmn_files(new_bpmn_files)
            ProcessInstanceProcessor.update_spiff_parser_with_all_process_dependency_files(
                parser, processed_identifiers
            )

    @staticmethod
    def get_spec(
        files: List[File], process_model_info: ProcessModelInfo
    ) -> Tuple[BpmnProcessSpec, IdToBpmnProcessSpecMapping]:
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
        if (
            process_model_info.primary_process_id is None
            or process_model_info.primary_process_id == ""
        ):
            raise (
                ApiError(
                    error_code="no_primary_bpmn_error",
                    message=(
                        "There is no primary BPMN process id defined for"
                        " process_model %s"
                    )
                    % process_model_info.id,
                )
            )
        ProcessInstanceProcessor.update_spiff_parser_with_all_process_dependency_files(
            parser
        )

        try:
            bpmn_process_spec = parser.get_spec(process_model_info.primary_process_id)

            # returns a dict of {process_id: bpmn_process_spec}, otherwise known as an IdToBpmnProcessSpecMapping
            subprocesses = parser.get_subprocess_specs(
                process_model_info.primary_process_id
            )
        except ValidationException as ve:
            raise ApiError(
                error_code="process_instance_validation_error",
                message="Failed to parse the Workflow Specification. "
                + "Error is '%s.'" % str(ve),
                file_name=ve.file_name,
                task_name=ve.name,
                task_id=ve.id,
                tag=ve.tag,
            ) from ve
        return (bpmn_process_spec, subprocesses)

    @staticmethod
    def status_of(bpmn_process_instance: BpmnWorkflow) -> ProcessInstanceStatus:
        """Status_of."""
        if bpmn_process_instance.is_completed():
            return ProcessInstanceStatus.complete
        user_tasks = bpmn_process_instance.get_ready_user_tasks()

        # if the process instance has status "waiting" it will get picked up
        # by background processing. when that happens it can potentially overwrite
        # human tasks which is bad because we cache them with the previous id's.
        # waiting_tasks = bpmn_process_instance.get_tasks(TaskState.WAITING)
        # if len(waiting_tasks) > 0:
        #     return ProcessInstanceStatus.waiting
        if len(user_tasks) > 0:
            return ProcessInstanceStatus.user_input_required
        else:
            return ProcessInstanceStatus.waiting

    def get_status(self) -> ProcessInstanceStatus:
        """Get_status."""
        the_status = self.status_of(self.bpmn_process_instance)
        # current_app.logger.debug(f"the_status: {the_status} for instance {self.process_instance_model.id}")
        return the_status

    # inspiration from https://github.com/collectiveidea/delayed_job_active_record/blob/master/lib/delayed/backend/active_record.rb
    # could consider borrowing their "cleanup all my locks when the app quits" idea as well and
    #   implement via https://docs.python.org/3/library/atexit.html
    def lock_process_instance(self, lock_prefix: str) -> None:
        locked_by = f"{lock_prefix}_{current_app.config['PROCESS_UUID']}"
        current_time_in_seconds = round(time.time())
        lock_expiry_in_seconds = (
            current_time_in_seconds
            - current_app.config["ALLOW_CONFISCATING_LOCK_AFTER_SECONDS"]
        )

        query_text = text(
            "UPDATE process_instance SET locked_at_in_seconds ="
            " :current_time_in_seconds, locked_by = :locked_by where id = :id AND"
            " (locked_by IS NULL OR locked_at_in_seconds < :lock_expiry_in_seconds);"
        ).execution_options(autocommit=True)
        result = db.engine.execute(
            query_text,
            id=self.process_instance_model.id,
            current_time_in_seconds=current_time_in_seconds,
            locked_by=locked_by,
            lock_expiry_in_seconds=lock_expiry_in_seconds,
        )
        # it seems like autocommit is working above (we see the statement in debug logs) but sqlalchemy doesn't
        #   seem to update properly so tell it to commit as well.
        # if we omit this line then querying the record from a unit test doesn't ever show the record as locked.
        db.session.commit()
        if result.rowcount < 1:
            raise ProcessInstanceIsAlreadyLockedError(
                f"Cannot lock process instance {self.process_instance_model.id}."
                "It has already been locked."
            )

    def unlock_process_instance(self, lock_prefix: str) -> None:
        locked_by = f"{lock_prefix}_{current_app.config['PROCESS_UUID']}"
        if self.process_instance_model.locked_by != locked_by:
            raise ProcessInstanceLockedBySomethingElseError(
                f"Cannot unlock process instance {self.process_instance_model.id}."
                f"It locked by {self.process_instance_model.locked_by}"
            )

        self.process_instance_model.locked_by = None
        self.process_instance_model.locked_at_in_seconds = None
        db.session.add(self.process_instance_model)
        db.session.commit()

    # messages have one correlation key (possibly wrong)
    # correlation keys may have many correlation properties
    def process_bpmn_messages(self) -> None:
        """Process_bpmn_messages."""
        bpmn_messages = self.bpmn_process_instance.get_bpmn_messages()
        for bpmn_message in bpmn_messages:
            # only message sends are in get_bpmn_messages
            message_model = MessageModel.query.filter_by(name=bpmn_message.name).first()
            if message_model is None:
                raise ApiError(
                    "invalid_message_name",
                    f"Invalid message name: {bpmn_message.name}.",
                )

            if not bpmn_message.correlations:
                raise ApiError(
                    "message_correlations_missing",
                    (
                        "Could not find any message correlations bpmn_message:"
                        f" {bpmn_message.name}"
                    ),
                )

            message_correlations = []
            for (
                message_correlation_key,
                message_correlation_properties,
            ) in bpmn_message.correlations.items():
                for (
                    message_correlation_property_identifier,
                    message_correlation_property_value,
                ) in message_correlation_properties.items():
                    message_correlation_property = (
                        MessageCorrelationPropertyModel.query.filter_by(
                            identifier=message_correlation_property_identifier,
                        ).first()
                    )
                    if message_correlation_property is None:
                        raise ApiError(
                            "message_correlations_missing_from_process",
                            (
                                "Could not find a known message correlation with"
                                f" identifier:{message_correlation_property_identifier}"
                            ),
                        )
                    message_correlations.append(
                        {
                            "message_correlation_property": (
                                message_correlation_property
                            ),
                            "name": message_correlation_key,
                            "value": message_correlation_property_value,
                        }
                    )
            message_instance = MessageInstanceModel(
                process_instance_id=self.process_instance_model.id,
                message_type="send",
                message_model_id=message_model.id,
                payload=bpmn_message.payload,
            )
            db.session.add(message_instance)
            db.session.commit()

            for message_correlation in message_correlations:
                message_correlation = MessageCorrelationModel(
                    process_instance_id=self.process_instance_model.id,
                    message_correlation_property_id=message_correlation[
                        "message_correlation_property"
                    ].id,
                    name=message_correlation["name"],
                    value=message_correlation["value"],
                )
                db.session.add(message_correlation)
                db.session.commit()
                message_correlation_message_instance = (
                    MessageCorrelationMessageInstanceModel(
                        message_instance_id=message_instance.id,
                        message_correlation_id=message_correlation.id,
                    )
                )
                db.session.add(message_correlation_message_instance)
            db.session.commit()

    def queue_waiting_receive_messages(self) -> None:
        """Queue_waiting_receive_messages."""
        waiting_tasks = self.get_all_waiting_tasks()
        for waiting_task in waiting_tasks:
            # if it's not something that can wait for a message, skip it
            if waiting_task.task_spec.__class__.__name__ not in [
                "IntermediateCatchEvent",
                "ReceiveTask",
            ]:
                continue

            # timer events are not related to messaging, so ignore them for these purposes
            if waiting_task.task_spec.event_definition.__class__.__name__.endswith(
                "TimerEventDefinition"
            ):
                continue

            message_model = MessageModel.query.filter_by(
                name=waiting_task.task_spec.event_definition.name
            ).first()
            if message_model is None:
                raise ApiError(
                    "invalid_message_name",
                    (
                        "Invalid message name:"
                        f" {waiting_task.task_spec.event_definition.name}."
                    ),
                )

            # Ensure we are only creating one message instance for each waiting message
            message_instance = MessageInstanceModel.query.filter_by(
                process_instance_id=self.process_instance_model.id,
                message_type="receive",
                message_model_id=message_model.id,
            ).first()
            if message_instance:
                continue

            message_instance = MessageInstanceModel(
                process_instance_id=self.process_instance_model.id,
                message_type="receive",
                message_model_id=message_model.id,
            )
            db.session.add(message_instance)

            for (
                spiff_correlation_property
            ) in waiting_task.task_spec.event_definition.correlation_properties:
                # NOTE: we may have to cycle through keys here
                # not sure yet if it's valid for a property to be associated with multiple keys
                correlation_key_name = spiff_correlation_property.correlation_keys[0]
                message_correlation = (
                    MessageCorrelationModel.query.filter_by(
                        process_instance_id=self.process_instance_model.id,
                        name=correlation_key_name,
                    )
                    .join(MessageCorrelationPropertyModel)
                    .filter_by(identifier=spiff_correlation_property.name)
                    .first()
                )
                message_correlation_message_instance = (
                    MessageCorrelationMessageInstanceModel(
                        message_instance_id=message_instance.id,
                        message_correlation_id=message_correlation.id,
                    )
                )
                db.session.add(message_correlation_message_instance)

            db.session.commit()

    def increment_spiff_step(self) -> None:
        """Spiff_step++."""
        spiff_step = self.process_instance_model.spiff_step or 0
        spiff_step += 1
        self.process_instance_model.spiff_step = spiff_step
        current_app.config["THREAD_LOCAL_DATA"].spiff_step = spiff_step
        db.session.add(self.process_instance_model)

    # TODO remove after done with the performance improvements
    # to use delete the _ prefix here and add it to the real def below
    def _do_engine_steps(self, exit_at: None = None, save: bool = False) -> None:
        """__do_engine_steps."""
        import cProfile
        from pstats import SortKey

        with cProfile.Profile() as pr:
            self._do_engine_steps(exit_at=exit_at, save=save)
        pr.print_stats(sort=SortKey.CUMULATIVE)

    def do_engine_steps(self, exit_at: None = None, save: bool = False) -> None:
        """Do_engine_steps."""
        step_details = []

        tasks_to_log = {
            "BPMN Task",
            "Script Task",
            "Service Task"
            # "End Event",
            # "Default Start Event",
            # "Exclusive Gateway",
            # "End Join",
            # "End Event",
            # "Default Throwing Event",
            # "Subprocess"
        }

        def should_log(task: SpiffTask) -> bool:
            if (
                task.task_spec.spec_type in tasks_to_log
                and not task.task_spec.name.endswith(".EndJoin")
            ):
                return True
            return False

        def will_complete_task(task: SpiffTask) -> None:
            if should_log(task):
                self.increment_spiff_step()

        def did_complete_task(task: SpiffTask) -> None:
            if should_log(task):
                self._script_engine.environment.revise_state_with_task_data(task)
                step_details.append(self.spiff_step_details_mapping())

        try:
            self.bpmn_process_instance.refresh_waiting_tasks()

            self.bpmn_process_instance.do_engine_steps(
                exit_at=exit_at,
                will_complete_task=will_complete_task,
                did_complete_task=did_complete_task,
            )

            if self.bpmn_process_instance.is_completed():
                self._script_engine.environment.finalize_result(
                    self.bpmn_process_instance
                )

            self.process_bpmn_messages()
            self.queue_waiting_receive_messages()

            db.session.bulk_insert_mappings(SpiffStepDetailsModel, step_details)
            spiff_logger = logging.getLogger("spiff")
            for handler in spiff_logger.handlers:
                if hasattr(handler, "bulk_insert_logs"):
                    handler.bulk_insert_logs()  # type: ignore
            db.session.commit()
        except SpiffWorkflowException as swe:
            raise ApiError.from_workflow_exception("task_error", str(swe), swe) from swe

        finally:
            if save:
                self.save()

    def cancel_notify(self) -> None:
        """Cancel_notify."""
        self.__cancel_notify(self.bpmn_process_instance)

    @staticmethod
    def __cancel_notify(bpmn_process_instance: BpmnWorkflow) -> None:
        """__cancel_notify."""
        try:
            # A little hackly, but make the bpmn_process_instance catch a cancel event.
            bpmn_process_instance.signal("cancel")  # generate a cancel signal.
            bpmn_process_instance.catch(CancelEventDefinition())
            # Due to this being static, can't save granular step details in this case
            bpmn_process_instance.do_engine_steps()
        except WorkflowTaskException as we:
            raise ApiError.from_workflow_exception("task_error", str(we), we) from we

    def user_defined_task_data(self, task_data: dict) -> dict:
        """UserDefinedTaskData."""
        return {k: v for k, v in task_data.items() if k != "current_user"}

    def check_task_data_size(self) -> None:
        """CheckTaskDataSize."""
        tasks_to_check = self.bpmn_process_instance.get_tasks(TaskState.FINISHED_MASK)
        task_data = [self.user_defined_task_data(task.data) for task in tasks_to_check]
        task_data_to_check = list(filter(len, task_data))

        try:
            task_data_len = len(json.dumps(task_data_to_check))
        except Exception:
            task_data_len = 0

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

    def serialize(self) -> str:
        """Serialize."""
        self.check_task_data_size()
        self.preserve_script_engine_state()
        return self._serializer.serialize_json(self.bpmn_process_instance)  # type: ignore

    def next_user_tasks(self) -> list[SpiffTask]:
        """Next_user_tasks."""
        return self.bpmn_process_instance.get_ready_user_tasks()  # type: ignore

    def next_task(self) -> SpiffTask:
        """Returns the next task that should be completed even if there are parallel tasks and multiple options are available.

        If the process_instance is complete
        it will return the final end task.
        """
        # If the whole blessed mess is done, return the end_event task in the tree
        # This was failing in the case of a call activity where we have an intermediate EndEvent
        # what we really want is the LAST EndEvent

        endtasks = []
        if self.bpmn_process_instance.is_completed():
            for task in SpiffTask.Iterator(
                self.bpmn_process_instance.task_tree, TaskState.ANY_MASK
            ):
                # Assure that we find the end event for this process_instance, and not for any sub-process_instances.
                if (
                    isinstance(task.task_spec, EndEvent)
                    and task.workflow == self.bpmn_process_instance
                ):
                    endtasks.append(task)
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
            else:
                return  # We have not tasks to return.

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
                if (
                    self.bpmn_process_instance.last_task
                    and task.parent == last_user_task.parent
                ):
                    return task

            return ready_tasks[0]

        # If there are no ready tasks, but the thing isn't complete yet, find the first non-complete task
        # and return that
        next_task = None
        for task in SpiffTask.Iterator(
            self.bpmn_process_instance.task_tree, TaskState.NOT_FINISHED_MASK
        ):
            next_task = task
        return next_task

    def completed_user_tasks(self) -> List[SpiffTask]:
        """Completed_user_tasks."""
        user_tasks = self.bpmn_process_instance.get_tasks(TaskState.COMPLETED)
        user_tasks.reverse()
        user_tasks = list(
            filter(
                lambda task: not self.bpmn_process_instance._is_engine_task(
                    task.task_spec
                ),
                user_tasks,
            )
        )
        return user_tasks  # type: ignore

    def complete_task(
        self, task: SpiffTask, human_task: HumanTaskModel, user: UserModel
    ) -> None:
        """Complete_task."""
        self.increment_spiff_step()
        self.bpmn_process_instance.complete_task_from_id(task.id)
        human_task.completed_by_user_id = user.id
        human_task.completed = True
        db.session.add(human_task)
        details_model = self.spiff_step_details()
        db.session.add(details_model)

        # this is the thing that actually commits the db transaction (on behalf of the other updates above as well)
        self.save()

    def get_data(self) -> dict[str, Any]:
        """Get_data."""
        return self.bpmn_process_instance.data  # type: ignore

    def get_current_data(self) -> dict[str, Any]:
        """Get the current data for the process.

        Return either the most recent task data or--if the process instance is complete--
        the process data.
        """
        if self.process_instance_model.status == "complete":
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
        """Get_process_instance_id."""
        return self.process_instance_model.id

    def get_ready_user_tasks(self) -> list[SpiffTask]:
        """Get_ready_user_tasks."""
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

    def get_all_user_tasks(self) -> List[SpiffTask]:
        """Get_all_user_tasks."""
        all_tasks = self.bpmn_process_instance.get_tasks(TaskState.ANY_MASK)
        return [
            t
            for t in all_tasks
            if not self.bpmn_process_instance._is_engine_task(t.task_spec)
        ]

    def get_all_completed_tasks(self) -> list[SpiffTask]:
        """Get_all_completed_tasks."""
        all_tasks = self.bpmn_process_instance.get_tasks(TaskState.ANY_MASK)
        return [
            t
            for t in all_tasks
            if not self.bpmn_process_instance._is_engine_task(t.task_spec)
            and t.state in [TaskState.COMPLETED, TaskState.CANCELLED]
        ]

    def get_all_waiting_tasks(self) -> list[SpiffTask]:
        """Get_all_ready_or_waiting_tasks."""
        all_tasks = self.bpmn_process_instance.get_tasks(TaskState.ANY_MASK)
        return [t for t in all_tasks if t.state in [TaskState.WAITING]]

    def get_all_ready_or_waiting_tasks(self) -> list[SpiffTask]:
        """Get_all_ready_or_waiting_tasks."""
        all_tasks = self.bpmn_process_instance.get_tasks(TaskState.ANY_MASK)
        return [t for t in all_tasks if t.state in [TaskState.WAITING, TaskState.READY]]

    @classmethod
    def get_task_by_bpmn_identifier(
        cls, bpmn_task_identifier: str, bpmn_process_instance: BpmnWorkflow
    ) -> Optional[SpiffTask]:
        """Get_task_by_id."""
        all_tasks = bpmn_process_instance.get_tasks(TaskState.ANY_MASK)
        for task in all_tasks:
            if task.task_spec.name == bpmn_task_identifier:
                return task
        return None

    def get_nav_item(self, task: SpiffTask) -> Any:
        """Get_nav_item."""
        for nav_item in self.bpmn_process_instance.get_nav_list():
            if nav_item["task_id"] == task.id:
                return nav_item
        return None

    def find_spec_and_field(self, spec_name: str, field_id: Union[str, int]) -> Any:
        """Tracks down a form field by name in the process_instance spec(s), Returns a tuple of the task, and form."""
        process_instances = [self.bpmn_process_instance]
        for task in self.bpmn_process_instance.get_ready_user_tasks():
            if task.process_instance not in process_instances:
                process_instances.append(task.process_instance)
        for process_instance in process_instances:
            for spec in process_instance.spec.task_specs.values():
                if spec.name == spec_name:
                    if not hasattr(spec, "form"):
                        raise ApiError(
                            "invalid_spec",
                            "The spec name you provided does not contain a form.",
                        )

                    for field in spec.form.fields:
                        if field.id == field_id:
                            return spec, field

                    raise ApiError(
                        "invalid_field",
                        f"The task '{spec_name}' has no field named '{field_id}'",
                    )

        raise ApiError(
            "invalid_spec",
            f"Unable to find a task in the process_instance called '{spec_name}'",
        )

    def terminate(self) -> None:
        """Terminate."""
        self.bpmn_process_instance.cancel()
        self.save()
        self.process_instance_model.status = "terminated"
        db.session.add(self.process_instance_model)
        db.session.commit()

    def suspend(self) -> None:
        """Suspend."""
        self.process_instance_model.status = ProcessInstanceStatus.suspended.value
        db.session.add(self.process_instance_model)
        db.session.commit()

    def resume(self) -> None:
        """Resume."""
        self.process_instance_model.status = ProcessInstanceStatus.waiting.value
        db.session.add(self.process_instance_model)
        db.session.commit()
