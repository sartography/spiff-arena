import _strptime  # type: ignore
import decimal
import glob
import json
import os
import re
import time
import traceback
import uuid
from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from datetime import timedelta
from typing import Any

import dateparser
import pytz
from lxml import etree  # type: ignore
from RestrictedPython import safe_globals  # type: ignore
from SpiffWorkflow.bpmn.exceptions import WorkflowTaskException  # type: ignore
from SpiffWorkflow.bpmn.script_engine import PythonScriptEngine  # type: ignore
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow  # type: ignore
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore
from SpiffWorkflow.util.deep_merge import DeepMerge  # type: ignore
from SpiffWorkflow.util.task import TaskState  # type: ignore

from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.script import Script
from spiffworkflow_backend.services.custom_parser import MyCustomParser
from spiffworkflow_backend.services.jinja_service import JinjaHelpers
from spiffworkflow_backend.services.process_instance_processor import CustomScriptEngineEnvironment
from spiffworkflow_backend.services.spec_file_service import SpecFileService

DEFAULT_NSMAP = {
    "bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL",
    "bpmndi": "http://www.omg.org/spec/BPMN/20100524/DI",
    "dc": "http://www.omg.org/spec/DD/20100524/DC",
}


"""
JSON file name:
    The name should be in format "test_BPMN_FILE_NAME.json".

BPMN_TASK_IDENTIIFER:
    can be either task bpmn identifier or in format:
    [BPMN_PROCESS_ID]:[TASK_BPMN_IDENTIFIER]
    example: 'BasicServiceTaskProcess:service_task_one'
    this allows for tasks to share bpmn identifiers across models
    which is useful for call activities

DATA for tasks:
    This is an array of task data. This allows for the task to
    be called multiple times and given different data each time.
    This is useful for testing loops where each iteration needs
    different input. The test will fail if the task is called
    multiple times without task data input for each call.

JSON file format:
{
    TEST_CASE_NAME: {
        "tasks": {
            BPMN_TASK_IDENTIIFER: {
            "data": [DATA]
            }
        },
        "expected_output_json": DATA
    }
}
"""


class UnrunnableTestCaseError(Exception):
    pass


class MissingBpmnFileForTestCaseError(Exception):
    pass


class NoTestCasesFoundError(Exception):
    pass


class MissingInputTaskDataError(Exception):
    pass


class UnsupporterRunnerDelegateGivenError(Exception):
    pass


class BpmnFileMissingExecutableProcessError(Exception):
    pass


@dataclass
class TestCaseErrorDetails:
    error_messages: list[str]
    task_error_line: str | None = None
    task_trace: list[str] | None = None
    task_bpmn_identifier: str | None = None
    task_bpmn_type: str | None = None
    task_bpmn_name: str | None = None
    task_line_number: int | None = None
    stacktrace: list[str] | None = None

    output_data: dict | None = None
    expected_data: dict | None = None


@dataclass
class TestCaseResult:
    passed: bool
    bpmn_file: str
    test_case_identifier: str
    test_case_error_details: TestCaseErrorDetails | None = None


def _import(name: str, glbls: dict[str, Any], *args: Any) -> None:
    if name not in glbls:
        raise ImportError(f"Import not allowed: {name}", name=name)


class ProcessModelTestRunnerScriptEngine(PythonScriptEngine):  # type: ignore
    def __init__(self, method_overrides: dict | None = None) -> None:
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

        # This will overwrite the standard builtins
        default_globals.update(safe_globals)
        default_globals["__builtins__"]["__import__"] = _import

        environment = CustomScriptEngineEnvironment.create(default_globals)
        self.method_overrides = method_overrides
        super().__init__(environment=environment)

    def _get_all_methods_for_context(self, external_context: dict[str, Any] | None, task: SpiffTask | None = None) -> dict:
        methods = {
            "get_process_initiator_user": lambda: {
                "username": "test_username_a",
                "tenant_specific_field_1": "test_tenant_specific_field_1_a",
            },
        }

        script_attributes_context = ScriptAttributesContext(
            task=task,
            environment_identifier="mocked-environment-identifier",
            process_instance_id=1,
            process_model_identifier="fake-test-process-model-identifier",
        )
        methods = Script.generate_augmented_list(script_attributes_context)

        if self.method_overrides:
            methods = {**methods, **self.method_overrides}

        if external_context:
            methods.update(external_context)

        return methods

    # Evaluate the given expression, within the context of the given task and
    # return the result.
    def evaluate(self, task: SpiffTask, expression: str, external_context: dict[str, Any] | None = None) -> Any:
        updated_context = self._get_all_methods_for_context(external_context, task)
        return super().evaluate(task, expression, updated_context)

    def execute(self, task: SpiffTask, script: str, external_context: Any = None) -> bool:
        if script:
            methods = self._get_all_methods_for_context(external_context, task)
            super().execute(task, script, methods)

        return True

    def call_service(
        self,
        operation_name: str,
        operation_params: dict[str, Any],
        spiff_task: SpiffTask,
    ) -> str:
        raise Exception("please override this service task in your bpmn unit test json")


class ProcessModelTestRunnerDelegate:
    """Abstract class for the process model test runner delegate.

    All delegates MUST inherit from this class.
    """

    def __init__(
        self,
        process_model_directory_path: str,
    ) -> None:
        self.process_model_directory_path = process_model_directory_path

    @abstractmethod
    def instantiate_executer(self, bpmn_file: str) -> BpmnWorkflow:
        raise NotImplementedError("method instantiate_executer must be implemented")

    @abstractmethod
    def execute_task(self, spiff_task: SpiffTask, task_data_for_submit: dict | None = None) -> None:
        raise NotImplementedError("method execute_task must be implemented")

    @abstractmethod
    def get_next_task(self, bpmn_process_instance: BpmnWorkflow) -> SpiffTask | None:
        raise NotImplementedError("method get_next_task must be implemented")


class ProcessModelTestRunnerMostlyPureSpiffDelegate(ProcessModelTestRunnerDelegate):
    def __init__(
        self,
        process_model_directory_path: str,
    ) -> None:
        super().__init__(process_model_directory_path)
        self.bpmn_processes_to_file_mappings: dict[str, str] = {}
        self.bpmn_files_to_called_element_mappings: dict[str, list[str]] = {}
        self._discover_process_model_processes()

    def instantiate_executer(self, bpmn_file: str) -> BpmnWorkflow:
        parser = MyCustomParser()

        # ensure we get the executable process for the primary bpmn file
        self._add_bpmn_file_to_parser(parser, bpmn_file)
        sub_parsers = list(parser.process_parsers.values())
        executable_process = None
        for sub_parser in sub_parsers:
            if sub_parser.process_executable:
                executable_process = sub_parser.bpmn_id
        if executable_process is None:
            raise BpmnFileMissingExecutableProcessError(f"Executable process cannot be found in {bpmn_file}. Test cannot run.")

        all_related = self._find_related_bpmn_files(bpmn_file)

        # get unique list of related files
        all_related = list(set(all_related))

        for related_file in all_related:
            self._add_bpmn_file_to_parser(parser, related_file)

        bpmn_process_spec = parser.get_spec(executable_process)
        subprocesses = parser.get_subprocess_specs(bpmn_process_spec.name)
        bpmn_process_instance = BpmnWorkflow(
            bpmn_process_spec,
            subprocess_specs=subprocesses,
        )
        return bpmn_process_instance

    def execute_task(self, spiff_task: SpiffTask, task_data_for_submit: dict | None = None) -> None:
        if task_data_for_submit is not None or spiff_task.task_spec.manual:
            if task_data_for_submit is not None:
                DeepMerge.merge(spiff_task.data, task_data_for_submit)
            spiff_task.complete()
        else:
            spiff_task.run()

    def get_next_task(self, bpmn_process_instance: BpmnWorkflow) -> SpiffTask | None:
        ready_tasks = list(bpmn_process_instance.get_tasks(state=TaskState.READY))
        if len(ready_tasks) > 0:
            return ready_tasks[0]
        return None

    def _add_bpmn_file_to_parser(self, parser: MyCustomParser, bpmn_file: str) -> None:
        related_file_etree = self._get_etree_from_bpmn_file(bpmn_file)
        parser.add_bpmn_xml(related_file_etree, filename=os.path.basename(bpmn_file))
        dmn_file_glob = os.path.join(os.path.dirname(bpmn_file), "*.dmn")
        parser.add_dmn_files_by_glob(dmn_file_glob)

    def _get_etree_from_bpmn_file(self, bpmn_file: str) -> etree._Element:
        with open(bpmn_file, "rb") as f_handle:
            data = f_handle.read()
        return SpecFileService.get_etree_from_xml_bytes(data)

    def _find_related_bpmn_files(self, bpmn_file: str) -> list[str]:
        related_bpmn_files = []
        if bpmn_file in self.bpmn_files_to_called_element_mappings:
            for bpmn_process_identifier in self.bpmn_files_to_called_element_mappings[bpmn_file]:
                if bpmn_process_identifier in self.bpmn_processes_to_file_mappings:
                    new_file = self.bpmn_processes_to_file_mappings[bpmn_process_identifier]
                    related_bpmn_files.append(new_file)
                    related_bpmn_files.extend(self._find_related_bpmn_files(new_file))
        return related_bpmn_files

    def _discover_process_model_processes(
        self,
    ) -> None:
        process_model_bpmn_file_glob = os.path.join(self.process_model_directory_path, "**", "*.bpmn")

        for file in glob.glob(process_model_bpmn_file_glob, recursive=True):
            file_norm = os.path.normpath(file)
            if file_norm not in self.bpmn_files_to_called_element_mappings:
                self.bpmn_files_to_called_element_mappings[file_norm] = []
            with open(file_norm, "rb") as f:
                file_contents = f.read()
            etree_xml_parser = etree.XMLParser(resolve_entities=False)

            # if we cannot load process model then ignore it since it can cause errors unrelated
            # to the test and if it is related, it will most likely be caught further along the test
            try:
                root = etree.fromstring(file_contents, parser=etree_xml_parser)  # noqa: S320
            except etree.XMLSyntaxError:
                continue

            call_activities = root.findall(".//bpmn:callActivity", namespaces=DEFAULT_NSMAP)
            for call_activity in call_activities:
                if "calledElement" in call_activity.attrib:
                    called_element = call_activity.attrib["calledElement"]
                    self.bpmn_files_to_called_element_mappings[file_norm].append(called_element)
            bpmn_process_element = root.find('.//bpmn:process[@isExecutable="true"]', namespaces=DEFAULT_NSMAP)
            if bpmn_process_element is not None:
                bpmn_process_identifier = bpmn_process_element.attrib["id"]
                self.bpmn_processes_to_file_mappings[bpmn_process_identifier] = file_norm


class ProcessModelTestRunner:
    """Runs the test case json files for a given process model directory.

    It searches for test case files recursively and will run all it finds by default.
    """

    def __init__(
        self,
        process_model_directory_path: str,
        process_model_test_runner_delegate_class: type = ProcessModelTestRunnerMostlyPureSpiffDelegate,
        process_model_directory_for_test_discovery: str | None = None,
        test_case_file: str | None = None,
        test_case_identifier: str | None = None,
    ) -> None:
        self.process_model_directory_path = process_model_directory_path
        self.process_model_directory_for_test_discovery = (
            process_model_directory_for_test_discovery or process_model_directory_path
        )
        self.test_case_file = test_case_file
        self.test_case_identifier = test_case_identifier

        if not issubclass(process_model_test_runner_delegate_class, ProcessModelTestRunnerDelegate):
            raise UnsupporterRunnerDelegateGivenError(
                "Process model test runner delegate must inherit from ProcessModelTestRunnerDelegate. Given"
                f" class '{process_model_test_runner_delegate_class}' does not"
            )

        self.process_model_test_runner_delegate = process_model_test_runner_delegate_class(process_model_directory_path)

        self.test_mappings = self._discover_process_model_test_cases()
        self.test_case_results: list[TestCaseResult] = []

        # keep track of the current task data index
        self.task_data_index: dict[str, int] = {}

    def all_test_cases_passed(self) -> bool:
        failed_tests = self.failing_tests()
        return len(failed_tests) < 1

    def failing_tests(self) -> list[TestCaseResult]:
        return [t for t in self.test_case_results if t.passed is False]

    def passing_tests(self) -> list[TestCaseResult]:
        return [t for t in self.test_case_results if t.passed is True]

    def failing_tests_formatted(self) -> str:
        formatted_tests = ["FAILING TESTS:"]
        for failing_test in self.failing_tests():
            msg = ""
            if failing_test.test_case_error_details is not None:
                msg = "\n\t\t".join(failing_test.test_case_error_details.error_messages)
            formatted_tests.append(f"\t{failing_test.bpmn_file}: {failing_test.test_case_identifier}: {msg}")
        return "\n".join(formatted_tests)

    def run(self) -> None:
        if len(self.test_mappings.items()) < 1:
            raise NoTestCasesFoundError(
                f"Could not find any test cases in given directory: {self.process_model_directory_for_test_discovery}"
            )
        for json_test_case_file, bpmn_file in self.test_mappings.items():
            with open(json_test_case_file) as f:
                json_file_contents = json.loads(f.read())

            for test_case_identifier, test_case_contents in json_file_contents.items():
                if self.test_case_identifier is None or test_case_identifier == self.test_case_identifier:
                    self.task_data_index = {}
                    try:
                        self.run_test_case(bpmn_file, test_case_identifier, test_case_contents)
                    except Exception as ex:
                        self._add_test_result(False, bpmn_file, test_case_identifier, exception=ex)

    def run_test_case(self, bpmn_file: str, test_case_identifier: str, test_case_contents: dict) -> None:
        bpmn_process_instance = self._instantiate_executer(bpmn_file)
        method_overrides = {}
        # mocking python functions within script tasks
        if "mocks" in test_case_contents:
            for method_name, mock_return_value in test_case_contents["mocks"].items():
                method_overrides[method_name] = lambda value=mock_return_value: value
        bpmn_process_instance.script_engine = ProcessModelTestRunnerScriptEngine(method_overrides=method_overrides)
        next_task = self._get_next_task(bpmn_process_instance)
        while next_task is not None:
            test_case_task_properties = None
            test_case_task_key = next_task.task_spec.bpmn_id
            if "tasks" in test_case_contents:
                if test_case_task_key not in test_case_contents["tasks"]:
                    # we may need to go to the top level workflow of a given bpmn file
                    test_case_task_key = f"{next_task.workflow.spec.name}:{next_task.task_spec.bpmn_id}"
                if test_case_task_key in test_case_contents["tasks"]:
                    test_case_task_properties = test_case_contents["tasks"][test_case_task_key]

            task_type = next_task.task_spec.__class__.__name__
            if task_type in ["ServiceTask", "UserTask"] and (
                test_case_task_properties is None or "data" not in test_case_task_properties
            ):
                raise UnrunnableTestCaseError(
                    f"Cannot run test case '{test_case_identifier}'. It requires task data for"
                    f" {next_task.task_spec.bpmn_id} because it is of type '{task_type}'"
                )
            self._execute_task(next_task, test_case_task_key, test_case_task_properties)
            bpmn_process_instance.refresh_waiting_tasks()
            next_task = self._get_next_task(bpmn_process_instance)

        error_message = None
        if bpmn_process_instance.is_completed() is False:
            error_message = {
                "error_messages": ["Expected process instance to complete but it did not."],
                "output_data": bpmn_process_instance.last_task.data,
                "task_bpmn_identifier": bpmn_process_instance.last_task.task_spec.bpmn_id,
                "task_bpmn_type": bpmn_process_instance.last_task.task_spec.__class__.__name__,
            }
        elif bpmn_process_instance.success is False:
            error_message = {
                "error_messages": ["Expected process instance to succeed but it did not."],
                "output_data": bpmn_process_instance.data,
            }
        elif test_case_contents["expected_output_json"] != bpmn_process_instance.data:
            error_message = {
                "error_messages": ["Expected output did not match actual output."],
                "expected_data": test_case_contents["expected_output_json"],
                "output_data": bpmn_process_instance.data,
            }
        self._add_test_result(error_message is None, bpmn_file, test_case_identifier, error_message)

    def _execute_task(
        self, spiff_task: SpiffTask, test_case_task_key: str | None, test_case_task_properties: dict | None
    ) -> None:
        task_data_for_submit = None

        # do not bother mocking data on multi-instance task types since the mocked data should go to the children
        # which will be the same type as the actual task like "UserTask" or "ManualTask".
        if (
            test_case_task_key
            and test_case_task_properties
            and "data" in test_case_task_properties
            and not self._is_multi_instance_task(spiff_task)
        ):
            if test_case_task_key not in self.task_data_index:
                self.task_data_index[test_case_task_key] = 0
            task_data_length = len(test_case_task_properties["data"])
            test_case_index = self.task_data_index[test_case_task_key]
            if task_data_length <= test_case_index:
                raise MissingInputTaskDataError(
                    f"Missing input task data for task: {test_case_task_key}. "
                    f"Only {task_data_length} given in the json but task was called {test_case_index + 1} times"
                )
            task_data_for_submit = test_case_task_properties["data"][test_case_index]
            self.task_data_index[test_case_task_key] += 1
        self.process_model_test_runner_delegate.execute_task(spiff_task, task_data_for_submit)

    def _is_multi_instance_task(self, spiff_task: SpiffTask) -> bool:
        return spiff_task.task_spec.__class__.__name__ in [
            "ParallelMultiInstanceTask",
            "SequentialMultiInstanceTask",
            "StandardLoopTask",
        ]

    def _get_next_task(self, bpmn_process_instance: BpmnWorkflow) -> SpiffTask | None:
        return self.process_model_test_runner_delegate.get_next_task(bpmn_process_instance)

    def _instantiate_executer(self, bpmn_file: str) -> BpmnWorkflow:
        return self.process_model_test_runner_delegate.instantiate_executer(bpmn_file)

    def _get_relative_path_of_bpmn_file(self, bpmn_file: str) -> str:
        return os.path.relpath(bpmn_file, start=self.process_model_directory_path)

    def _exception_to_test_case_error_details(self, exception: Exception | WorkflowTaskException) -> TestCaseErrorDetails:
        error_messages = str(exception).split("\n")
        test_case_error_details = TestCaseErrorDetails(error_messages=error_messages)
        if isinstance(exception, WorkflowTaskException):
            test_case_error_details.task_error_line = exception.error_line
            test_case_error_details.task_trace = exception.task_trace
            test_case_error_details.task_line_number = exception.line_number
            test_case_error_details.task_bpmn_identifier = exception.task_spec.bpmn_id
            test_case_error_details.task_bpmn_name = exception.task_spec.bpmn_name
        else:
            test_case_error_details.stacktrace = traceback.format_exc().split("\n")

        return test_case_error_details

    def _add_test_result(
        self,
        passed: bool,
        bpmn_file: str,
        test_case_identifier: str,
        error_messages: dict | None = None,
        exception: Exception | None = None,
    ) -> None:
        test_case_error_details = None
        if exception is not None:
            test_case_error_details = self._exception_to_test_case_error_details(exception)
        elif error_messages:
            test_case_error_details = TestCaseErrorDetails(**error_messages)

        bpmn_file_relative = self._get_relative_path_of_bpmn_file(bpmn_file)
        test_result = TestCaseResult(
            passed=passed,
            bpmn_file=bpmn_file_relative,
            test_case_identifier=test_case_identifier,
            test_case_error_details=test_case_error_details,
        )
        self.test_case_results.append(test_result)

    def _discover_process_model_test_cases(
        self,
    ) -> dict[str, str]:
        test_mappings = {}
        json_test_file_glob = os.path.join(self.process_model_directory_for_test_discovery, "**", "test_*.json")

        for file in glob.glob(json_test_file_glob, recursive=True):
            file_norm = os.path.normpath(file)
            file_dir = os.path.dirname(file_norm)
            json_file_name = os.path.basename(file_norm)
            if self.test_case_file is None or json_file_name == self.test_case_file:
                bpmn_file_name = re.sub(r"^test_(.*)\.json", r"\1.bpmn", json_file_name)
                bpmn_file_path = os.path.join(file_dir, bpmn_file_name)
                if os.path.isfile(bpmn_file_path):
                    test_mappings[file_norm] = bpmn_file_path
                else:
                    raise MissingBpmnFileForTestCaseError(
                        f"Cannot find a matching bpmn file for test case json file: '{file_norm}'"
                    )
        return test_mappings


class ProcessModelTestRunnerBackendDelegate(ProcessModelTestRunnerMostlyPureSpiffDelegate):
    pass


class ProcessModelTestRunnerService:
    def __init__(
        self,
        process_model_directory_path: str,
        test_case_file: str | None = None,
        test_case_identifier: str | None = None,
    ) -> None:
        self.process_model_test_runner = ProcessModelTestRunner(
            process_model_directory_path,
            test_case_file=test_case_file,
            test_case_identifier=test_case_identifier,
            process_model_test_runner_delegate_class=ProcessModelTestRunnerBackendDelegate,
        )

    def run(self) -> None:
        self.process_model_test_runner.run()
