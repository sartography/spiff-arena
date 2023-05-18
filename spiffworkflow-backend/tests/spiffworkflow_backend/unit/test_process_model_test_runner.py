import os
from typing import Any
from typing import Optional

import pytest
from flask import current_app
from flask import Flask
from pytest_mock import MockerFixture
from tests.spiffworkflow_backend.helpers.base_test import BaseTest

from spiffworkflow_backend.models.task import TaskModel  # noqa: F401
from spiffworkflow_backend.services.file_system_service import FileSystemService
from spiffworkflow_backend.services.process_model_test_runner_service import NoTestCasesFoundError
from spiffworkflow_backend.services.process_model_test_runner_service import ProcessModelTestRunner


class TestProcessModelTestRunner(BaseTest):
    def test_can_test_a_simple_process_model(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
        with_mocked_root_path: Any,
    ) -> None:
        process_model_test_runner = self._run_model_tests("basic_script_task")
        assert len(process_model_test_runner.test_case_results) == 1

    def test_will_raise_if_no_tests_found(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
        with_mocked_root_path: Any,
    ) -> None:
        process_model_test_runner = ProcessModelTestRunner(os.path.join(FileSystemService.root_path(), "DNE"))
        with pytest.raises(NoTestCasesFoundError):
            process_model_test_runner.run()
        assert process_model_test_runner.all_test_cases_passed(), process_model_test_runner.test_case_results

    def test_can_test_multiple_process_models_with_all_passing_tests(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
        with_mocked_root_path: Any,
    ) -> None:
        process_model_test_runner = self._run_model_tests()
        assert len(process_model_test_runner.test_case_results) > 1

    def test_can_test_multiple_process_models_with_failing_tests(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
        with_mocked_root_path: Any,
    ) -> None:
        process_model_test_runner = self._run_model_tests(parent_directory="failing_tests")
        assert len(process_model_test_runner.test_case_results) == 1

    def test_can_test_process_model_call_activity(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
        with_mocked_root_path: Any,
    ) -> None:
        process_model_test_runner = self._run_model_tests(bpmn_process_directory_name="basic_call_activity")
        assert len(process_model_test_runner.test_case_results) == 1

    def test_can_test_process_model_with_service_task(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
        with_mocked_root_path: Any,
    ) -> None:
        process_model_test_runner = self._run_model_tests(bpmn_process_directory_name="basic_service_task")
        assert len(process_model_test_runner.test_case_results) == 1

    def _run_model_tests(
        self, bpmn_process_directory_name: Optional[str] = None, parent_directory: str = "passing_tests"
    ) -> ProcessModelTestRunner:
        base_process_model_dir_path_segments = [FileSystemService.root_path(), parent_directory]
        path_segments = base_process_model_dir_path_segments
        if bpmn_process_directory_name:
            path_segments = path_segments + [bpmn_process_directory_name]
        process_model_test_runner = ProcessModelTestRunner(
            process_model_directory_path=os.path.join(*base_process_model_dir_path_segments),
            process_model_directory_for_test_discovery=os.path.join(*path_segments),
        )
        process_model_test_runner.run()

        all_tests_expected_to_pass = parent_directory == "passing_tests"
        assert (
            process_model_test_runner.all_test_cases_passed() is all_tests_expected_to_pass
        ), process_model_test_runner.failing_tests_formatted()
        return process_model_test_runner

    @pytest.fixture()
    def with_mocked_root_path(self, mocker: MockerFixture) -> None:
        path = os.path.join(
            current_app.instance_path,
            "..",
            "..",
            "tests",
            "data",
            "bpmn_unit_test_process_models",
        )
        mocker.patch.object(FileSystemService, attribute="root_path", return_value=path)
