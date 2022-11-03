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

import dateparser
import pytz
from flask import current_app
from flask_bpmn.api.api_error import ApiError
from flask_bpmn.models.db import db
from lxml import etree  # type: ignore
from RestrictedPython import safe_globals  # type: ignore
from SpiffWorkflow.bpmn.exceptions import WorkflowTaskExecException  # type: ignore
from SpiffWorkflow.bpmn.parser.ValidationException import ValidationException  # type: ignore
from SpiffWorkflow.bpmn.PythonScriptEngine import Box  # type: ignore
from SpiffWorkflow.bpmn.PythonScriptEngine import PythonScriptEngine
from SpiffWorkflow.bpmn.serializer.workflow import BpmnWorkflowSerializer  # type: ignore
from SpiffWorkflow.bpmn.specs.BpmnProcessSpec import BpmnProcessSpec  # type: ignore
from SpiffWorkflow.bpmn.specs.events.EndEvent import EndEvent  # type: ignore
from SpiffWorkflow.bpmn.specs.events.event_definitions import CancelEventDefinition  # type: ignore
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow  # type: ignore
from SpiffWorkflow.dmn.parser.BpmnDmnParser import BpmnDmnParser  # type: ignore
from SpiffWorkflow.dmn.serializer.task_spec_converters import BusinessRuleTaskConverter  # type: ignore
from SpiffWorkflow.exceptions import WorkflowException  # type: ignore
from SpiffWorkflow.serializer.exceptions import MissingSpecError  # type: ignore
from SpiffWorkflow.spiff.parser.process import SpiffBpmnParser  # type: ignore
from SpiffWorkflow.spiff.serializer.task_spec_converters import BoundaryEventConverter  # type: ignore
from SpiffWorkflow.spiff.serializer.task_spec_converters import (
    CallActivityTaskConverter,
)
from SpiffWorkflow.spiff.serializer.task_spec_converters import EndEventConverter
from SpiffWorkflow.spiff.serializer.task_spec_converters import (
    IntermediateCatchEventConverter,
)
from SpiffWorkflow.spiff.serializer.task_spec_converters import (
    IntermediateThrowEventConverter,
)
from SpiffWorkflow.spiff.serializer.task_spec_converters import ManualTaskConverter
from SpiffWorkflow.spiff.serializer.task_spec_converters import NoneTaskConverter
from SpiffWorkflow.spiff.serializer.task_spec_converters import ReceiveTaskConverter
from SpiffWorkflow.spiff.serializer.task_spec_converters import ScriptTaskConverter
from SpiffWorkflow.spiff.serializer.task_spec_converters import SendTaskConverter
from SpiffWorkflow.spiff.serializer.task_spec_converters import ServiceTaskConverter
from SpiffWorkflow.spiff.serializer.task_spec_converters import StartEventConverter
from SpiffWorkflow.spiff.serializer.task_spec_converters import SubWorkflowTaskConverter
from SpiffWorkflow.spiff.serializer.task_spec_converters import (
    TransactionSubprocessConverter,
)
from SpiffWorkflow.spiff.serializer.task_spec_converters import UserTaskConverter
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore
from SpiffWorkflow.task import TaskState
from SpiffWorkflow.util.deep_merge import DeepMerge  # type: ignore

from spiffworkflow_backend.models.active_task import ActiveTaskModel
from spiffworkflow_backend.models.active_task_user import ActiveTaskUserModel
from spiffworkflow_backend.models.bpmn_process_id_lookup import BpmnProcessIdLookup
from spiffworkflow_backend.models.file import File
from spiffworkflow_backend.models.file import FileType
from spiffworkflow_backend.models.group import GroupModel
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
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.models.script_attributes_context import (
    ScriptAttributesContext,
)
from spiffworkflow_backend.models.spiff_step_details import SpiffStepDetailsModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.models.user import UserModelSchema
from spiffworkflow_backend.scripts.script import Script
from spiffworkflow_backend.services.file_system_service import FileSystemService
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.service_task_service import ServiceTaskDelegate
from spiffworkflow_backend.services.spec_file_service import SpecFileService
from spiffworkflow_backend.services.user_service import UserService

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


class CustomBpmnScriptEngine(PythonScriptEngine):  # type: ignore
    """This is a custom script processor that can be easily injected into Spiff Workflow.

    It will execute python code read in from the bpmn.  It will also make any scripts in the
    scripts directory available for execution.
    """

    def __init__(self) -> None:
        """__init__."""
        default_globals = {
            "timedelta": timedelta,
            "datetime": datetime,
            "dateparser": dateparser,
            "pytz": pytz,
            "time": time,
            "decimal": decimal,
            "_strptime": _strptime,
        }

        # This will overwrite the standard builtins
        default_globals.update(safe_globals)
        default_globals["__builtins__"]["__import__"] = _import

        super().__init__(default_globals=default_globals)

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

    def evaluate(self, task: SpiffTask, expression: str) -> Any:
        """Evaluate."""
        return self._evaluate(expression, task.data, task)

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
                raise ProcessInstanceProcessorError(
                    "Error evaluating expression: "
                    "'%s', exception: %s" % (expression, str(exception)),
                ) from exception
            else:
                raise WorkflowTaskExecException(
                    task,
                    "Error evaluating expression "
                    "'%s', %s" % (expression, str(exception)),
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
            raise WorkflowTaskExecException(task, f" {script}, {e}", e) from e

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


class MyCustomParser(BpmnDmnParser):  # type: ignore
    """A BPMN and DMN parser that can also parse spiffworkflow-specific extensions."""

    OVERRIDE_PARSER_CLASSES = BpmnDmnParser.OVERRIDE_PARSER_CLASSES
    OVERRIDE_PARSER_CLASSES.update(SpiffBpmnParser.OVERRIDE_PARSER_CLASSES)


IdToBpmnProcessSpecMapping = NewType(
    "IdToBpmnProcessSpecMapping", dict[str, BpmnProcessSpec]
)


class ProcessInstanceProcessor:
    """ProcessInstanceProcessor."""

    _script_engine = CustomBpmnScriptEngine()
    SERIALIZER_VERSION = "1.0-spiffworkflow-backend"
    wf_spec_converter = BpmnWorkflowSerializer.configure_workflow_spec_converter(
        [
            BoundaryEventConverter,
            BusinessRuleTaskConverter,
            CallActivityTaskConverter,
            EndEventConverter,
            IntermediateCatchEventConverter,
            IntermediateThrowEventConverter,
            ManualTaskConverter,
            NoneTaskConverter,
            ReceiveTaskConverter,
            ScriptTaskConverter,
            SendTaskConverter,
            ServiceTaskConverter,
            StartEventConverter,
            SubWorkflowTaskConverter,
            TransactionSubprocessConverter,
            UserTaskConverter,
        ]
    )
    _serializer = BpmnWorkflowSerializer(wf_spec_converter, version=SERIALIZER_VERSION)

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
            f"{process_instance_model.process_group_identifier}/"
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
                process_instance_model.process_model_identifier,
                process_instance_model.process_group_identifier,
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
        self.process_group_identifier = process_instance_model.process_group_identifier

        try:
            self.bpmn_process_instance = self.__get_bpmn_process_instance(
                process_instance_model,
                bpmn_process_spec,
                validate_only,
                subprocesses=subprocesses,
            )
            self.bpmn_process_instance.script_engine = self._script_engine

            self.add_user_info_to_process_instance(self.bpmn_process_instance)

            if self.PROCESS_INSTANCE_ID_KEY not in self.bpmn_process_instance.data:
                if not process_instance_model.id:
                    db.session.add(process_instance_model)
                    # If the model is new, and has no id, save it, write it into the process_instance model
                    # and save it again.  In this way, the workflow process is always aware of the
                    # database model to which it is associated, and scripts running within the model
                    # can then load data as needed.
                self.bpmn_process_instance.data[
                    ProcessInstanceProcessor.PROCESS_INSTANCE_ID_KEY
                ] = process_instance_model.id
                self.save()

        except MissingSpecError as ke:
            raise ApiError(
                error_code="unexpected_process_instance_structure",
                message="Failed to deserialize process_instance"
                " '%s'  due to a mis-placed or missing task '%s'"
                % (self.process_model_identifier, str(ke)),
            ) from ke

    @classmethod
    def get_process_model_and_subprocesses(
        cls, process_model_identifier: str, process_group_identifier: str
    ) -> Tuple[BpmnProcessSpec, IdToBpmnProcessSpecMapping]:
        """Get_process_model_and_subprocesses."""
        process_model_info = ProcessModelService().get_process_model(
            process_model_identifier, process_group_identifier
        )
        if process_model_info is None:
            raise (
                ApiError(
                    "process_model_not_found",
                    f"The given process model was not found: {process_group_identifier}/{process_model_identifier}.",
                )
            )
        spec_files = SpecFileService.get_files(process_model_info)
        return cls.get_spec(spec_files, process_model_info)

    @classmethod
    def get_bpmn_process_instance_from_process_model(
        cls, process_model_identifier: str, process_group_identifier: str
    ) -> BpmnWorkflow:
        """Get_all_bpmn_process_identifiers_for_process_model."""
        (bpmn_process_spec, subprocesses) = cls.get_process_model_and_subprocesses(
            process_model_identifier,
            process_group_identifier,
        )
        return cls.get_bpmn_process_instance_from_workflow_spec(
            bpmn_process_spec, subprocesses
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
        return BpmnWorkflow(
            spec,
            script_engine=ProcessInstanceProcessor._script_engine,
            subprocess_specs=subprocesses,
        )

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
                raise (err)
            finally:
                spiff_logger.setLevel(original_spiff_logger_log_level)

            bpmn_process_instance.script_engine = (
                ProcessInstanceProcessor._script_engine
            )
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
            raise (NoPotentialOwnersForTaskError(message))

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
                f"No users found in task data lane owner list for lane: {task_lane}. "
                f"The user list used: {task.data['lane_owners'][task_lane]}",
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

    def save_spiff_step_details(self) -> None:
        """SaveSpiffStepDetails."""
        bpmn_json = self.serialize()
        wf_json = json.loads(bpmn_json)
        task_json = "{}"
        if "tasks" in wf_json:
            task_json = json.dumps(wf_json["tasks"])

        # TODO want to just save the tasks, something wasn't immediately working
        # so after the flow works with the full wf_json revisit this
        task_json = wf_json
        details_model = SpiffStepDetailsModel(
            process_instance_id=self.process_instance_model.id,
            spiff_step=self.process_instance_model.spiff_step or 1,
            task_json=task_json,
            timestamp=round(time.time()),
            completed_by_user_id=self.current_user().id,
        )
        db.session.add(details_model)
        db.session.commit()

    def save(self) -> None:
        """Saves the current state of this processor to the database."""
        self.process_instance_model.bpmn_json = self.serialize()

        complete_states = [TaskState.CANCELLED, TaskState.COMPLETED]
        user_tasks = list(self.get_all_user_tasks())
        self.process_instance_model.status = self.get_status().value
        self.process_instance_model.total_tasks = len(user_tasks)
        self.process_instance_model.completed_tasks = sum(
            1 for t in user_tasks if t.state in complete_states
        )

        if self.process_instance_model.start_in_seconds is None:
            self.process_instance_model.start_in_seconds = round(time.time())

        if self.process_instance_model.end_in_seconds is None:
            if self.bpmn_process_instance.is_completed():
                self.process_instance_model.end_in_seconds = round(time.time())

        active_tasks = ActiveTaskModel.query.filter_by(
            process_instance_id=self.process_instance_model.id
        ).all()
        if len(active_tasks) > 0:
            for at in active_tasks:
                db.session.delete(at)

        db.session.add(self.process_instance_model)
        db.session.commit()

        ready_or_waiting_tasks = self.get_all_ready_or_waiting_tasks()
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

                process_model_display_name = ""
                process_model_info = self.process_model_service.get_process_model(
                    self.process_instance_model.process_model_identifier
                )
                if process_model_info is not None:
                    process_model_display_name = process_model_info.display_name

                active_task = ActiveTaskModel(
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
                db.session.add(active_task)
                db.session.commit()

                for potential_owner_id in potential_owner_hash["potential_owner_ids"]:
                    active_task_user = ActiveTaskUserModel(
                        user_id=potential_owner_id, active_task_id=active_task.id
                    )
                    db.session.add(active_task_user)
                db.session.commit()

    @staticmethod
    def get_parser() -> MyCustomParser:
        """Get_parser."""
        parser = MyCustomParser()
        return parser

    @staticmethod
    def backfill_missing_bpmn_process_id_lookup_records(
        bpmn_process_identifier: str,
    ) -> Optional[str]:
        """Backfill_missing_bpmn_process_id_lookup_records."""
        process_models = ProcessModelService().get_process_models()
        for process_model in process_models:
            if process_model.primary_file_name:
                etree_element = SpecFileService.get_etree_element_from_file_name(
                    process_model, process_model.primary_file_name
                )
                bpmn_process_identifiers = []

                try:
                    bpmn_process_identifiers = (
                        SpecFileService.get_executable_bpmn_process_identifiers(
                            etree_element
                        )
                    )
                except ValidationException:
                    # ignore validation errors here
                    pass

                if bpmn_process_identifier in bpmn_process_identifiers:
                    SpecFileService.store_bpmn_process_identifiers(
                        process_model,
                        process_model.primary_file_name,
                        etree_element,
                    )
                    return FileSystemService.full_path_to_process_model_file(
                        process_model, process_model.primary_file_name
                    )
        return None

    @staticmethod
    def bpmn_file_full_path_from_bpmn_process_identifier(
        bpmn_process_identifier: str,
    ) -> str:
        """Bpmn_file_full_path_from_bpmn_process_identifier."""
        bpmn_process_id_lookup = BpmnProcessIdLookup.query.filter_by(
            bpmn_process_identifier=bpmn_process_identifier
        ).first()
        bpmn_file_full_path = None
        if bpmn_process_id_lookup is None:
            bpmn_file_full_path = ProcessInstanceProcessor.backfill_missing_bpmn_process_id_lookup_records(
                bpmn_process_identifier
            )
        else:
            bpmn_file_full_path = os.path.join(
                FileSystemService.root_path(),
                bpmn_process_id_lookup.bpmn_file_relative_path,
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
            if file.type == FileType.bpmn.value:
                bpmn: etree.Element = etree.fromstring(data)
                parser.add_bpmn_xml(bpmn, filename=file.name)
            elif file.type == FileType.dmn.value:
                dmn: etree.Element = etree.fromstring(data)
                parser.add_dmn_xml(dmn, filename=file.name)
        if (
            process_model_info.primary_process_id is None
            or process_model_info.primary_process_id == ""
        ):
            raise (
                ApiError(
                    error_code="no_primary_bpmn_error",
                    message="There is no primary BPMN process id defined for process_model %s"
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
                file_name=ve.filename,
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
        waiting_tasks = bpmn_process_instance.get_tasks(TaskState.WAITING)
        if len(waiting_tasks) > 0:
            return ProcessInstanceStatus.waiting
        if len(user_tasks) > 0:
            return ProcessInstanceStatus.user_input_required
        else:
            return ProcessInstanceStatus.waiting

    def get_status(self) -> ProcessInstanceStatus:
        """Get_status."""
        return self.status_of(self.bpmn_process_instance)

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
                    f"Could not find any message correlations bpmn_message: {bpmn_message.name}",
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
                            "Could not find a known message correlation with identifier:"
                            f"{message_correlation_property_identifier}",
                        )
                    message_correlations.append(
                        {
                            "message_correlation_property": message_correlation_property,
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
            if waiting_task.task_spec.event_definition.__class__.__name__ in [
                "TimerEventDefinition",
            ]:
                continue

            message_model = MessageModel.query.filter_by(
                name=waiting_task.task_spec.event_definition.name
            ).first()
            if message_model is None:
                raise ApiError(
                    "invalid_message_name",
                    f"Invalid message name: {waiting_task.task_spec.event_definition.name}.",
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
        db.session.commit()

    def do_engine_steps(self, exit_at: None = None, save: bool = False) -> None:
        """Do_engine_steps."""
        try:
            self.bpmn_process_instance.refresh_waiting_tasks(
                will_refresh_task=lambda t: self.increment_spiff_step(),
                did_refresh_task=lambda t: self.save_spiff_step_details(),
            )

            self.bpmn_process_instance.do_engine_steps(
                exit_at=exit_at,
                will_complete_task=lambda t: self.increment_spiff_step(),
                did_complete_task=lambda t: self.save_spiff_step_details(),
            )

            self.process_bpmn_messages()
            self.queue_waiting_receive_messages()

        except WorkflowTaskExecException as we:
            raise ApiError.from_workflow_exception("task_error", str(we), we) from we

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
        except WorkflowTaskExecException as we:
            raise ApiError.from_workflow_exception("task_error", str(we), we) from we

    def serialize(self) -> str:
        """Serialize."""
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

    def complete_task(self, task: SpiffTask) -> None:
        """Complete_task."""
        self.increment_spiff_step()
        self.bpmn_process_instance.complete_task_from_id(task.id)
        self.save_spiff_step_details()

    def get_data(self) -> dict[str, Any]:
        """Get_data."""
        return self.bpmn_process_instance.data  # type: ignore

    def get_current_data(self) -> dict[str, Any]:
        """Get the current data for the process.

        Return either most recent task data or the process data
        if the process instance is complete
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
