import pytest
from flask.app import Flask
from flask.testing import FlaskClient
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.workflow_execution_service import WorkflowExecutionServiceError

from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestRestrictedScriptEngine(BaseTest):
    def test_dot_notation_with_open_file(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_model = load_test_spec(
            "test_group/dangerous",
            bpmn_file_name="read_etc_passwd.bpmn",
            process_model_source_directory="dangerous-scripts",
        )
        process_instance = self.create_process_instance_from_process_model(process_model)
        processor = ProcessInstanceProcessor(process_instance)

        with pytest.raises(WorkflowExecutionServiceError) as exception:
            processor.do_engine_steps(save=True)
        assert "name 'open' is not defined" in str(exception.value)

    def test_dot_notation_with_import_module(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_model = load_test_spec(
            "test_group/dangerous",
            bpmn_file_name="read_env.bpmn",
            process_model_source_directory="dangerous-scripts",
        )
        process_instance = self.create_process_instance_from_process_model(process_model)
        processor = ProcessInstanceProcessor(process_instance)

        with pytest.raises(WorkflowExecutionServiceError) as exception:
            processor.do_engine_steps(save=True)
        assert "Import not allowed: os" in str(exception.value)
