import glob
import json
import os
import re
from dataclasses import dataclass
from typing import Any
from typing import Callable
from typing import Optional

from lxml import etree  # type: ignore
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow  # type: ignore
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore
from SpiffWorkflow.task import TaskState

from spiffworkflow_backend.services.custom_parser import MyCustomParser
from spiffworkflow_backend.services.spec_file_service import SpecFileService


# workflow json for test case
# 1. default action is load xml from disk and use spiff like normal and get back workflow json
# 2. do stuff from disk cache

# find all process models
# find all json test cases for each
# for each test case, fire up something like spiff
# for each task, if there is something special in the test case definition,
#   do it (provide data for user task, mock service task, etc)
# when the thing is complete, check workflow data against expected data


class UnrunnableTestCaseError(Exception):
    pass


class MissingBpmnFileForTestCaseError(Exception):
    pass


class NoTestCasesFoundError(Exception):
    pass


@dataclass
class TestCaseResult:
    passed: bool
    bpmn_file: str
    test_case_name: str
    error: Optional[str] = None


DEFAULT_NSMAP = {
    'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL',
    'bpmndi': 'http://www.omg.org/spec/BPMN/20100524/DI',
    'dc': 'http://www.omg.org/spec/DD/20100524/DC',
}


# input:
#   json_file:
# {
#     [TEST_CASE_NAME]: {
#         "tasks": {
#             [BPMN_TASK_IDENTIIFER]: {
#               "data": [DATA]
#             }
#         },
#         "expected_output_json": [DATA]
#     }
# }
class ProcessModelTestRunner:
    """Generic test runner code. May move into own library at some point.

    KEEP THIS GENERIC. do not add backend specific code here.
    """

    def __init__(
        self,
        process_model_directory_path: str,
        process_model_directory_for_test_discovery: Optional[str] = None,
        instantiate_executer_callback: Optional[Callable[[str], Any]] = None,
        execute_task_callback: Optional[Callable[[Any, Optional[dict]], Any]] = None,
        get_next_task_callback: Optional[Callable[[Any], Any]] = None,
    ) -> None:
        self.process_model_directory_path = process_model_directory_path
        self.process_model_directory_for_test_discovery = process_model_directory_for_test_discovery or process_model_directory_path
        self.instantiate_executer_callback = instantiate_executer_callback
        self.execute_task_callback = execute_task_callback
        self.get_next_task_callback = get_next_task_callback

        self.test_case_results: list[TestCaseResult] = []
        self.bpmn_processes_to_file_mappings: dict[str, str] = {}
        self.bpmn_files_to_called_element_mappings: dict[str, list[str]] = {}

        self.test_mappings = self._discover_process_model_test_cases()
        self._discover_process_model_processes()

    def all_test_cases_passed(self) -> bool:
        failed_tests = [t for t in self.test_case_results if t.passed is False]
        return len(failed_tests) < 1

    def run(self) -> None:
        if len(self.test_mappings.items()) < 1:
            raise NoTestCasesFoundError(f"Could not find any test cases in given directory: {self.process_model_directory_for_test_discovery}")
        for json_test_case_file, bpmn_file in self.test_mappings.items():
            with open(json_test_case_file) as f:
                json_file_contents = json.loads(f.read())

            for test_case_name, test_case_contents in json_file_contents.items():
                try:
                    self.run_test_case(bpmn_file, test_case_name, test_case_contents)
                except Exception as ex:
                    self._add_test_result(False, bpmn_file, test_case_name, f"Syntax error: {str(ex)}")

    def run_test_case(self, bpmn_file: str, test_case_name: str, test_case_contents: dict) -> None:
        bpmn_process_instance = self._instantiate_executer(bpmn_file)
        next_task = self._get_next_task(bpmn_process_instance)
        while next_task is not None:
            test_case_task_properties = None
            if "tasks" in test_case_contents:
                if next_task.task_spec.bpmn_id in test_case_contents["tasks"]:
                    test_case_task_properties = test_case_contents["tasks"][next_task.task_spec.bpmn_id]

            task_type = next_task.task_spec.__class__.__name__
            if task_type in ["ServiceTask", "UserTask", "CallActivity"] and test_case_task_properties is None:
                raise UnrunnableTestCaseError(
                    f"Cannot run test case '{test_case_name}'. It requires task data for"
                    f" {next_task.task_spec.bpmn_id} because it is of type '{task_type}'"
                )
            self._execute_task(next_task, test_case_task_properties)
            next_task = self._get_next_task(bpmn_process_instance)
        test_passed = test_case_contents["expected_output_json"] == bpmn_process_instance.data
        error_message = None
        if test_passed is False:
            error_message = (
                f"Expected output did not match actual output:"
                f"\nexpected: {test_case_contents['expected_output_json']}"
                f"\nactual: {bpmn_process_instance.data}"
            )
        self._add_test_result(test_passed, bpmn_file, test_case_name, error_message)

    def _discover_process_model_test_cases(
        self,
    ) -> dict[str, str]:
        test_mappings = {}

        json_test_file_glob = os.path.join(self.process_model_directory_for_test_discovery, "**", "test_*.json")

        for file in glob.glob(json_test_file_glob, recursive=True):
            file_norm = os.path.normpath(file)
            file_dir = os.path.dirname(file_norm)
            json_file_name = os.path.basename(file_norm)
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
            with open(file_norm, 'rb') as f:
                file_contents = f.read()
            etree_xml_parser = etree.XMLParser(resolve_entities=False)
            root = etree.fromstring(file_contents, parser=etree_xml_parser)
            call_activities = root.findall('.//bpmn:callActivity', namespaces=DEFAULT_NSMAP)
            for call_activity in call_activities:
                called_element = call_activity.attrib['calledElement']
                self.bpmn_files_to_called_element_mappings[file_norm].append(called_element)
            bpmn_process_element = root.find('.//bpmn:process[@isExecutable="true"]', namespaces=DEFAULT_NSMAP)
            bpmn_process_identifier = bpmn_process_element.attrib['id']
            self.bpmn_processes_to_file_mappings[bpmn_process_identifier] = file_norm

    def _execute_task(self, spiff_task: SpiffTask, test_case_task_properties: Optional[dict]) -> None:
        if self.execute_task_callback:
            self.execute_task_callback(spiff_task, test_case_task_properties)
        self._default_execute_task(spiff_task, test_case_task_properties)

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

    def _default_execute_task(self, spiff_task: SpiffTask, test_case_task_properties: Optional[dict]) -> None:
        if spiff_task.task_spec.manual or spiff_task.task_spec.__class__.__name__ == 'ServiceTask':
            if test_case_task_properties and 'data' in test_case_task_properties:
                spiff_task.update_data(test_case_task_properties['data'])
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

    def _get_etree_from_bpmn_file(self, bpmn_file: str) -> etree.Element:
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

    def _add_test_result(self, passed: bool, bpmn_file: str, test_case_name: str, error: Optional[str] = None) -> None:
        bpmn_file_relative = os.path.relpath(bpmn_file, start=self.process_model_directory_path)
        test_result = TestCaseResult(
            passed=passed,
            bpmn_file=bpmn_file_relative,
            test_case_name=test_case_name,
            error=error,
        )
        self.test_case_results.append(test_result)


class BpmnFileMissingExecutableProcessError(Exception):
    pass


class ProcessModelTestRunnerService:
    def __init__(self, process_model_directory_path: str) -> None:
        self.process_model_test_runner = ProcessModelTestRunner(
            process_model_directory_path,
            # instantiate_executer_callback=self._instantiate_executer_callback,
            # execute_task_callback=self._execute_task_callback,
            # get_next_task_callback=self._get_next_task_callback,
        )

    def run(self) -> None:
        self.process_model_test_runner.run()
