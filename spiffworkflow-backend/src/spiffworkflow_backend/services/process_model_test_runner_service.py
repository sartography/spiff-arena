import glob
import json
import os
import re
import traceback
from dataclasses import dataclass
from typing import Any
from typing import Callable
from typing import Optional
from typing import Union

from lxml import etree  # type: ignore
from SpiffWorkflow.bpmn.exceptions import WorkflowTaskException  # type: ignore
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow  # type: ignore
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore
from SpiffWorkflow.task import TaskState

from spiffworkflow_backend.services.custom_parser import MyCustomParser


class UnrunnableTestCaseError(Exception):
    pass


class MissingBpmnFileForTestCaseError(Exception):
    pass


class NoTestCasesFoundError(Exception):
    pass


class MissingInputTaskData(Exception):
    pass


@dataclass
class TestCaseErrorDetails:
    error_messages: list[str]
    task_error_line: Optional[str] = None
    task_trace: Optional[list[str]] = None
    task_bpmn_identifier: Optional[str] = None
    task_bpmn_name: Optional[str] = None
    task_line_number: Optional[int] = None
    stacktrace: Optional[list[str]] = None


@dataclass
class TestCaseResult:
    passed: bool
    bpmn_file: str
    test_case_identifier: str
    test_case_error_details: Optional[TestCaseErrorDetails] = None


DEFAULT_NSMAP = {
    "bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL",
    "bpmndi": "http://www.omg.org/spec/BPMN/20100524/DI",
    "dc": "http://www.omg.org/spec/DD/20100524/DC",
}


"""
JSON file name:
    The name should be in format "test_BPMN_FILE_NAME_IT_TESTS.json".

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


class ProcessModelTestRunner:
    """Generic test runner code. May move into own library at some point.

    KEEP THIS GENERIC. do not add backend specific code here.
    """

    def __init__(
        self,
        process_model_directory_path: str,
        process_model_directory_for_test_discovery: Optional[str] = None,
        instantiate_executer_callback: Optional[Callable[[str], Any]] = None,
        execute_task_callback: Optional[Callable[[Any, Optional[str], Optional[dict]], Any]] = None,
        get_next_task_callback: Optional[Callable[[Any], Any]] = None,
        test_case_file: Optional[str] = None,
        test_case_identifier: Optional[str] = None,
    ) -> None:
        self.process_model_directory_path = process_model_directory_path
        self.process_model_directory_for_test_discovery = (
            process_model_directory_for_test_discovery or process_model_directory_path
        )
        self.instantiate_executer_callback = instantiate_executer_callback
        self.execute_task_callback = execute_task_callback
        self.get_next_task_callback = get_next_task_callback
        self.test_case_file = test_case_file
        self.test_case_identifier = test_case_identifier

        # keep track of the current task data index
        self.task_data_index: dict[str, int] = {}

        self.test_case_results: list[TestCaseResult] = []
        self.bpmn_processes_to_file_mappings: dict[str, str] = {}
        self.bpmn_files_to_called_element_mappings: dict[str, list[str]] = {}

        self.test_mappings = self._discover_process_model_test_cases()
        self._discover_process_model_processes()

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
            if task_type in ["ServiceTask", "UserTask", "CallActivity"] and test_case_task_properties is None:
                raise UnrunnableTestCaseError(
                    f"Cannot run test case '{test_case_identifier}'. It requires task data for"
                    f" {next_task.task_spec.bpmn_id} because it is of type '{task_type}'"
                )
            self._execute_task(next_task, test_case_task_key, test_case_task_properties)
            next_task = self._get_next_task(bpmn_process_instance)

        error_message = None
        if bpmn_process_instance.is_completed() is False:
            error_message = [
                "Expected process instance to complete but it did not.",
                f"Final data was: {bpmn_process_instance.last_task.data}",
                f"Last task bpmn id: {bpmn_process_instance.last_task.task_spec.bpmn_id}",
                f"Last task type: {bpmn_process_instance.last_task.task_spec.__class__.__name__}",
            ]
        elif bpmn_process_instance.success is False:
            error_message = [
                "Expected process instance to succeed but it did not.",
                f"Final data was: {bpmn_process_instance.data}",
            ]
        elif test_case_contents["expected_output_json"] != bpmn_process_instance.data:
            error_message = [
                "Expected output did not match actual output:",
                f"expected: {test_case_contents['expected_output_json']}",
                f"actual: {bpmn_process_instance.data}",
            ]
        self._add_test_result(error_message is None, bpmn_file, test_case_identifier, error_message)

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
                root = etree.fromstring(file_contents, parser=etree_xml_parser)
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

    def _execute_task(
        self, spiff_task: SpiffTask, test_case_task_key: Optional[str], test_case_task_properties: Optional[dict]
    ) -> None:
        if self.execute_task_callback:
            self.execute_task_callback(spiff_task, test_case_task_key, test_case_task_properties)
        self._default_execute_task(spiff_task, test_case_task_key, test_case_task_properties)

    def _get_next_task(self, bpmn_process_instance: BpmnWorkflow) -> Optional[SpiffTask]:
        if self.get_next_task_callback:
            return self.get_next_task_callback(bpmn_process_instance)
        return self._default_get_next_task(bpmn_process_instance)

    def _instantiate_executer(self, bpmn_file: str) -> BpmnWorkflow:
        if self.instantiate_executer_callback:
            return self.instantiate_executer_callback(bpmn_file)
        return self._default_instantiate_executer(bpmn_file)

    def _default_get_next_task(self, bpmn_process_instance: BpmnWorkflow) -> Optional[SpiffTask]:
        ready_tasks = list([t for t in bpmn_process_instance.get_tasks(TaskState.READY)])
        if len(ready_tasks) > 0:
            return ready_tasks[0]
        return None

    def _default_execute_task(
        self, spiff_task: SpiffTask, test_case_task_key: Optional[str], test_case_task_properties: Optional[dict]
    ) -> None:
        if spiff_task.task_spec.manual or spiff_task.task_spec.__class__.__name__ == "ServiceTask":
            if test_case_task_key and test_case_task_properties and "data" in test_case_task_properties:
                if test_case_task_key not in self.task_data_index:
                    self.task_data_index[test_case_task_key] = 0
                task_data_length = len(test_case_task_properties["data"])
                test_case_index = self.task_data_index[test_case_task_key]
                if task_data_length <= test_case_index:
                    raise MissingInputTaskData(
                        f"Missing input task data for task: {test_case_task_key}. "
                        f"Only {task_data_length} given in the json but task was called {test_case_index + 1} times"
                    )
                spiff_task.update_data(test_case_task_properties["data"][test_case_index])
                self.task_data_index[test_case_task_key] += 1
            spiff_task.complete()
        else:
            spiff_task.run()

    def _find_related_bpmn_files(self, bpmn_file: str) -> list[str]:
        related_bpmn_files = []
        if bpmn_file in self.bpmn_files_to_called_element_mappings:
            for bpmn_process_identifier in self.bpmn_files_to_called_element_mappings[bpmn_file]:
                if bpmn_process_identifier in self.bpmn_processes_to_file_mappings:
                    new_file = self.bpmn_processes_to_file_mappings[bpmn_process_identifier]
                    related_bpmn_files.append(new_file)
                    related_bpmn_files.extend(self._find_related_bpmn_files(new_file))
        return related_bpmn_files

    def _get_etree_from_bpmn_file(self, bpmn_file: str) -> etree._Element:
        data = None
        with open(bpmn_file, "rb") as f_handle:
            data = f_handle.read()
        etree_xml_parser = etree.XMLParser(resolve_entities=False)
        return etree.fromstring(data, parser=etree_xml_parser)

    def _default_instantiate_executer(self, bpmn_file: str) -> BpmnWorkflow:
        parser = MyCustomParser()
        bpmn_file_etree = self._get_etree_from_bpmn_file(bpmn_file)
        parser.add_bpmn_xml(bpmn_file_etree, filename=os.path.basename(bpmn_file))
        all_related = self._find_related_bpmn_files(bpmn_file)
        for related_file in all_related:
            related_file_etree = self._get_etree_from_bpmn_file(related_file)
            parser.add_bpmn_xml(related_file_etree, filename=os.path.basename(related_file))
        sub_parsers = list(parser.process_parsers.values())
        executable_process = None
        for sub_parser in sub_parsers:
            if sub_parser.process_executable:
                executable_process = sub_parser.bpmn_id
        if executable_process is None:
            raise BpmnFileMissingExecutableProcessError(
                f"Executable process cannot be found in {bpmn_file}. Test cannot run."
            )
        bpmn_process_spec = parser.get_spec(executable_process)
        bpmn_process_instance = BpmnWorkflow(bpmn_process_spec)
        return bpmn_process_instance

    def _get_relative_path_of_bpmn_file(self, bpmn_file: str) -> str:
        return os.path.relpath(bpmn_file, start=self.process_model_directory_path)

    def _exception_to_test_case_error_details(
        self, exception: Union[Exception, WorkflowTaskException]
    ) -> TestCaseErrorDetails:
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
        error_messages: Optional[list[str]] = None,
        exception: Optional[Exception] = None,
    ) -> None:
        test_case_error_details = None
        if exception is not None:
            test_case_error_details = self._exception_to_test_case_error_details(exception)
        elif error_messages:
            test_case_error_details = TestCaseErrorDetails(error_messages=error_messages)

        bpmn_file_relative = self._get_relative_path_of_bpmn_file(bpmn_file)
        test_result = TestCaseResult(
            passed=passed,
            bpmn_file=bpmn_file_relative,
            test_case_identifier=test_case_identifier,
            test_case_error_details=test_case_error_details,
        )
        self.test_case_results.append(test_result)


class BpmnFileMissingExecutableProcessError(Exception):
    pass


class ProcessModelTestRunnerService:
    def __init__(
        self,
        process_model_directory_path: str,
        test_case_file: Optional[str] = None,
        test_case_identifier: Optional[str] = None,
    ) -> None:
        self.process_model_test_runner = ProcessModelTestRunner(
            process_model_directory_path,
            test_case_file=test_case_file,
            test_case_identifier=test_case_identifier,
            # instantiate_executer_callback=self._instantiate_executer_callback,
            # execute_task_callback=self._execute_task_callback,
            # get_next_task_callback=self._get_next_task_callback,
        )

    def run(self) -> None:
        self.process_model_test_runner.run()
