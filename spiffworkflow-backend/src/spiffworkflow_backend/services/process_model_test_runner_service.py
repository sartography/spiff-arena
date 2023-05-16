from typing import List, Optional
from dataclasses import dataclass
import json
from SpiffWorkflow.task import Task as SpiffTask # type: ignore
from SpiffWorkflow.task import TaskState
from lxml import etree # type: ignore
from spiffworkflow_backend.services.spec_file_service import SpecFileService
from spiffworkflow_backend.services.custom_parser import MyCustomParser
from typing import Callable
import re
import glob
from spiffworkflow_backend.models.process_model import ProcessModelInfo
import os
from spiffworkflow_backend.services.file_system_service import FileSystemService
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow  # type: ignore


# workflow json for test case
# 1. default action is load xml from disk and use spiff like normal and get back workflow json
# 2. do stuff from disk cache

# find all process models
# find all json test cases for each
# for each test case, fire up something like spiff
# for each task, if there is something special in the test case definition, do it (provide data for user task, mock service task, etc)
# when the thing is complete, check workflow data against expected data


class UnrunnableTestCaseError(Exception):
    pass


class MissingBpmnFileForTestCaseError(Exception):
    pass


@dataclass
class TestCaseResult:
    passed: bool
    test_case_name: str
    error: Optional[str] = None


# input:
#   json_file:
# {
#     [TEST_CASE_NAME]: {
#         "tasks": {
#             [BPMN_TASK_IDENTIIFER]: [DATA]
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
        instantiate_executer_callback: Callable[[str], any],
        execute_task_callback: Callable[[any, Optional[dict]], any],
        get_next_task_callback: Callable[[any], any],
    ) -> None:
        self.process_model_directory_path = process_model_directory_path
        self.test_mappings = self._discover_process_model_directories()
        self.instantiate_executer_callback = instantiate_executer_callback
        self.execute_task_callback = execute_task_callback
        self.get_next_task_callback = get_next_task_callback

        self.test_case_results = []

    def all_test_cases_passed(self) -> bool:
        failed_tests = [t for t in self.test_case_results if t.passed is False]
        return len(failed_tests) < 1

    def run(self) -> None:
        for json_test_case_file, bpmn_file in self.test_mappings.items():
            with open(json_test_case_file, 'rt') as f:
                json_file_contents = json.loads(f.read())

            for test_case_name, test_case_contents in json_file_contents.items():
                try:
                    self.run_test_case(bpmn_file, test_case_name, test_case_contents)
                except Exception as ex:
                    self.test_case_results.append(TestCaseResult(
                        passed=False,
                        test_case_name=test_case_name,
                        error=f"Syntax error: {str(ex)}",
                    ))

    def run_test_case(self, bpmn_file: str, test_case_name: str, test_case_contents: dict) -> None:
        bpmn_process_instance = self.instantiate_executer_callback(bpmn_file)
        next_task = self.get_next_task_callback(bpmn_process_instance)
        while next_task is not None:
            test_case_json = None
            if 'tasks' in test_case_contents:
                if next_task.task_spec.bpmn_id in test_case_contents['tasks']:
                    test_case_json = test_case_contents['tasks'][next_task.task_spec.bpmn_id]

            task_type = next_task.task_spec.__class__.__name__
            if task_type in ["ServiceTask", "UserTask"] and test_case_json is None:
                raise UnrunnableTestCaseError(
                        f"Cannot run test case '{test_case_name}'. It requires task data for {next_task.task_spec.bpmn_id} because it is of type '{task_type}'"
                )
            self.execute_task_callback(next_task, test_case_json)
            next_task = self.get_next_task_callback(bpmn_process_instance)
        test_passed = test_case_contents['expected_output_json'] == bpmn_process_instance.data
        self.test_case_results.append(TestCaseResult(
            passed=test_passed,
            test_case_name=test_case_name,
        ))

    def _discover_process_model_directories(
        self,
    ) -> dict[str, str]:
        test_mappings = {}

        json_test_file_glob = os.path.join(self.process_model_directory_path, "**", "test_*.json")

        for file in glob.glob(json_test_file_glob, recursive=True):
            file_dir = os.path.dirname(file)
            json_file_name = os.path.basename(file)
            bpmn_file_name = re.sub(r'^test_(.*)\.json', r'\1.bpmn', json_file_name)
            bpmn_file_path = os.path.join(file_dir, bpmn_file_name)
            if os.path.isfile(bpmn_file_path):
                test_mappings[file] = bpmn_file_path
            else:
                raise MissingBpmnFileForTestCaseError(f"Cannot find a matching bpmn file for test case json file: '{file}'")
        return test_mappings


class BpmnFileMissingExecutableProcessError(Exception):
    pass


class ProcessModelTestRunnerService:
    def __init__(
        self,
        process_model_directory_path: str
    ) -> None:
        self.process_model_test_runner = ProcessModelTestRunner(
            process_model_directory_path,
            instantiate_executer_callback=self._instantiate_executer_callback,
            execute_task_callback=self._execute_task_callback,
            get_next_task_callback=self._get_next_task_callback,
        )

    def run(self) -> None:
        self.process_model_test_runner.run()

    def _execute_task_callback(self, spiff_task: SpiffTask, _test_case_json: Optional[dict]) -> None:
        spiff_task.run()

    def _get_next_task_callback(self, bpmn_process_instance: BpmnWorkflow) -> Optional[SpiffTask]:
        engine_steps = self._get_ready_engine_steps(bpmn_process_instance)
        if len(engine_steps) > 0:
            return engine_steps[0]
        return None

    def _get_ready_engine_steps(self, bpmn_process_instance: BpmnWorkflow) -> list[SpiffTask]:
        tasks = list([t for t in bpmn_process_instance.get_tasks(TaskState.READY) if not t.task_spec.manual])

        if len(tasks) > 0:
            tasks = [tasks[0]]

        return tasks

    def _instantiate_executer_callback(self, bpmn_file) -> BpmnWorkflow:
        parser = MyCustomParser()
        data = None
        with open(bpmn_file, "rb") as f_handle:
            data = f_handle.read()
        bpmn: etree.Element = SpecFileService.get_etree_from_xml_bytes(data)
        parser.add_bpmn_xml(bpmn, filename=os.path.basename(bpmn_file))
        sub_parsers = list(parser.process_parsers.values())
        executable_process = None
        for sub_parser in sub_parsers:
            if sub_parser.process_executable:
                executable_process = sub_parser.bpmn_id
        if executable_process is None:
            raise BpmnFileMissingExecutableProcessError(f"Executable process cannot be found in {bpmn_file}. Test cannot run.")
        bpmn_process_spec = parser.get_spec(executable_process)
        bpmn_process_instance = BpmnWorkflow(bpmn_process_spec)
        return bpmn_process_instance
