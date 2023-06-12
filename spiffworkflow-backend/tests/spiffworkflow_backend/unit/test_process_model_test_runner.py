import os

import pytest
from flask import Flask
from flask import current_app
from spiffworkflow_backend.services.process_model_test_runner_service import NoTestCasesFoundError
from spiffworkflow_backend.services.process_model_test_runner_service import ProcessModelTestRunner
from spiffworkflow_backend.services.process_model_test_runner_service import UnsupporterRunnerDelegateGivenError

from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestProcessModelTestRunner(BaseTest):
    def test_can_test_a_simple_process_model(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_model_test_runner = self._run_model_tests("script-task")
        assert len(process_model_test_runner.test_case_results) == 1

    def test_will_raise_if_no_tests_found(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_model_test_runner = ProcessModelTestRunner(os.path.join(self.root_path(), "DNE"))
        with pytest.raises(NoTestCasesFoundError):
            process_model_test_runner.run()
        assert process_model_test_runner.all_test_cases_passed(), process_model_test_runner.test_case_results

    def test_will_raise_if_bad_delegate_is_given(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        with pytest.raises(UnsupporterRunnerDelegateGivenError):
            ProcessModelTestRunner(
                os.path.join(self.root_path(), "DNE"), process_model_test_runner_delegate_class=NoTestCasesFoundError
            )

    def test_can_test_multiple_process_models_with_all_passing_tests(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_model_test_runner = self._run_model_tests()
        assert len(process_model_test_runner.test_case_results) > 1

    def test_can_test_multiple_process_models_with_failing_tests(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_model_test_runner = self._run_model_tests(parent_directory="expected-to-fail")
        assert len(process_model_test_runner.test_case_results) == 3

    def test_can_test_process_model_with_multiple_files(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_model_test_runner = self._run_model_tests(bpmn_process_directory_name="multiple-test-files")
        assert len(process_model_test_runner.test_case_results) == 3

        process_model_test_runner = self._run_model_tests(
            bpmn_process_directory_name="multiple-test-files", test_case_file="test_a.json"
        )
        assert len(process_model_test_runner.test_case_results) == 1

        process_model_test_runner = self._run_model_tests(
            bpmn_process_directory_name="multiple-test-files", test_case_file="test_b.json"
        )
        assert len(process_model_test_runner.test_case_results) == 2

        process_model_test_runner = self._run_model_tests(
            bpmn_process_directory_name="multiple-test-files",
            test_case_file="test_b.json",
            test_case_identifier="test_case_2",
        )
        assert len(process_model_test_runner.test_case_results) == 1

    def test_can_test_process_model_call_activity(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_model_test_runner = self._run_model_tests(bpmn_process_directory_name="call-activity")
        assert len(process_model_test_runner.test_case_results) == 1

    def test_can_test_process_model_with_service_task(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_model_test_runner = self._run_model_tests(bpmn_process_directory_name="service-task")
        assert len(process_model_test_runner.test_case_results) == 1

    def test_can_test_process_model_with_loopback_to_user_task(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_model_test_runner = self._run_model_tests(bpmn_process_directory_name="loopback-to-user-task")
        assert len(process_model_test_runner.test_case_results) == 1

    def _run_model_tests(
        self,
        bpmn_process_directory_name: str | None = None,
        parent_directory: str = "expected-to-pass",
        test_case_file: str | None = None,
        test_case_identifier: str | None = None,
    ) -> ProcessModelTestRunner:
        base_process_model_dir_path_segments = [self.root_path(), parent_directory]
        path_segments = base_process_model_dir_path_segments
        if bpmn_process_directory_name:
            path_segments = path_segments + [bpmn_process_directory_name]
        process_model_test_runner = ProcessModelTestRunner(
            process_model_directory_path=os.path.join(*base_process_model_dir_path_segments),
            process_model_directory_for_test_discovery=os.path.join(*path_segments),
            test_case_file=test_case_file,
            test_case_identifier=test_case_identifier,
        )
        process_model_test_runner.run()

        all_tests_expected_to_pass = parent_directory == "expected-to-pass"
        assert (
            process_model_test_runner.all_test_cases_passed() is all_tests_expected_to_pass
        ), process_model_test_runner.failing_tests_formatted()
        return process_model_test_runner

    def root_path(self) -> str:
        return os.path.join(
            current_app.instance_path,
            "..",
            "..",
            "tests",
            "data",
            "bpmn_unit_test_process_models",
        )
