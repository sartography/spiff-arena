from flask.app import Flask
from flask.testing import FlaskClient
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.script_unit_test_runner import PythonScriptContext
from spiffworkflow_backend.services.script_unit_test_runner import ScriptUnitTestRunner

from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestScriptUnitTestRunner(BaseTest):
    def test_takes_data_and_returns_expected_result(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        app.config["THREAD_LOCAL_DATA"].process_instance_id = None

        process_group_id = "test_logging_spiff_logger"
        process_model_id = "simple_script"
        process_model_identifier = f"{process_group_id}/{process_model_id}"
        load_test_spec(
            process_model_identifier,
            bpmn_file_name=process_model_id,
            process_model_source_directory=process_model_id,
        )
        bpmn_process_instance = ProcessInstanceProcessor.get_bpmn_process_instance_from_process_model(process_model_identifier)
        task = ProcessInstanceProcessor.get_task_by_bpmn_identifier("Activity_CalculateNewData", bpmn_process_instance)
        assert task is not None

        input_context: PythonScriptContext = {"a": 1}
        expected_output_context: PythonScriptContext = {"a": 2}
        script = "a = 2"

        unit_test_result = ScriptUnitTestRunner.run_with_script_and_pre_post_contexts(
            script, input_context, expected_output_context
        )

        assert unit_test_result.result
        assert unit_test_result.context == {"a": 2}

    def test_fails_when_expected_output_does_not_match_actual_output(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        app.config["THREAD_LOCAL_DATA"].process_instance_id = None

        process_group_id = "test_logging_spiff_logger"
        process_model_id = "simple_script"
        process_model_identifier = f"{process_group_id}/{process_model_id}"
        load_test_spec(
            process_model_identifier,
            bpmn_file_name=process_model_id,
            process_model_source_directory=process_model_id,
        )
        bpmn_process_instance = ProcessInstanceProcessor.get_bpmn_process_instance_from_process_model(process_model_identifier)
        task = ProcessInstanceProcessor.get_task_by_bpmn_identifier("Activity_CalculateNewData", bpmn_process_instance)
        assert task is not None

        input_context: PythonScriptContext = {"a": 1}
        expected_output_context: PythonScriptContext = {"a": 2, "b": 3}
        script = "a = 2"

        unit_test_result = ScriptUnitTestRunner.run_with_script_and_pre_post_contexts(
            script, input_context, expected_output_context
        )

        assert unit_test_result.result is not True
        assert unit_test_result.context == {"a": 2}

    def test_script_with_unit_tests_when_hey_is_passed_in(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        app.config["THREAD_LOCAL_DATA"].process_instance_id = None

        process_group_id = "script_with_unit_tests"
        process_model_id = "script_with_unit_tests"
        process_model_identifier = f"{process_group_id}/{process_model_id}"
        load_test_spec(
            process_model_identifier,
            bpmn_file_name=process_model_id,
            process_model_source_directory=process_model_id,
        )
        bpmn_process_instance = ProcessInstanceProcessor.get_bpmn_process_instance_from_process_model(process_model_identifier)
        task = ProcessInstanceProcessor.get_task_by_bpmn_identifier("script_with_unit_test_id", bpmn_process_instance)
        assert task is not None

        expected_output_context: PythonScriptContext = {"hey": True}

        unit_test_result = ScriptUnitTestRunner.run_test(task, "sets_hey_to_true_if_hey_is_false")

        assert unit_test_result.result
        assert unit_test_result.context == expected_output_context

    def test_script_with_unit_tests_when_hey_is_not_passed_in(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        app.config["THREAD_LOCAL_DATA"].process_instance_id = None

        process_group_id = "script_with_unit_tests"
        process_model_id = "script_with_unit_tests"
        process_model_identifier = f"{process_group_id}/{process_model_id}"

        load_test_spec(
            process_model_identifier,
            bpmn_file_name=process_model_id,
            process_model_source_directory=process_model_id,
        )
        bpmn_process_instance = ProcessInstanceProcessor.get_bpmn_process_instance_from_process_model(process_model_identifier)
        task = ProcessInstanceProcessor.get_task_by_bpmn_identifier("script_with_unit_test_id", bpmn_process_instance)
        assert task is not None

        expected_output_context: PythonScriptContext = {"something_else": True}

        unit_test_result = ScriptUnitTestRunner.run_test(task, "sets_something_else_if_no_hey")

        assert unit_test_result.result
        assert unit_test_result.context == expected_output_context
