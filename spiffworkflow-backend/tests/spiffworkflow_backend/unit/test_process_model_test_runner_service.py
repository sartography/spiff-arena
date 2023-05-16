from flask import Flask
import pytest
import os
from flask import current_app
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.services.file_system_service import FileSystemService
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.process_model_test_runner_service import ProcessModelTestRunner, ProcessModelTestRunnerService
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec
from pytest_mock import MockerFixture

from spiffworkflow_backend.models.bpmn_process import BpmnProcessModel
from spiffworkflow_backend.models.bpmn_process_definition import BpmnProcessDefinitionModel
from spiffworkflow_backend.models.task import TaskModel  # noqa: F401
from spiffworkflow_backend.models.task_definition import TaskDefinitionModel
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.task_service import TaskService


class TestProcessModelTestRunnerService(BaseTest):
    def test_can_test_a_simple_process_model(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
        with_mocked_root_path: any,
    ) -> None:
        test_runner_service = ProcessModelTestRunnerService(os.path.join(FileSystemService.root_path(), 'basic_script_task'))
        test_runner_service.run()
        assert test_runner_service.process_model_test_runner.all_test_cases_passed()

    def test_can_test_multiple_process_models(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
        with_mocked_root_path: any,
    ) -> None:
        test_runner_service = ProcessModelTestRunnerService(FileSystemService.root_path())
        test_runner_service.run()
        assert test_runner_service.process_model_test_runner.all_test_cases_passed() is False

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
        mocker.patch.object(FileSystemService, attribute='root_path', return_value=path)
