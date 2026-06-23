from unittest.mock import MagicMock
from unittest.mock import patch

from flask.app import Flask

from spiffworkflow_backend.interfaces import PotentialOwnerIdList
from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestTaskAvailableProcessModelTrigger(BaseTest):
    @patch(
        "spiffworkflow_backend.services.process_instance_processor.ProcessInstanceProcessor.setup_processor_with_process_instance"
    )
    @patch("spiffworkflow_backend.services.process_instance_service.ProcessInstanceService.create_and_run_process_instance")
    @patch("spiffworkflow_backend.services.process_model_service.ProcessModelService.get_process_model")
    def test_trigger_task_available_process_model_injects_only_task_guid(
        self,
        mock_get_process_model: MagicMock,
        mock_create_and_run: MagicMock,
        mock_setup: MagicMock,
        app: Flask,
    ) -> None:
        # Setup
        process_initiator = UserModel(id=1, username="testuser", service="test", service_id="testuser")
        process_instance = ProcessInstanceModel(id=123, process_initiator=process_initiator)
        processor = ProcessInstanceProcessor(process_instance)
        processor.process_instance_model = process_instance

        human_task = HumanTaskModel(process_instance_id=123, task_guid="task_guid_456", task_id="task_guid_456")

        task_available_pm_id = "task_available_model"
        mock_task_available_pm = MagicMock()
        mock_get_process_model.return_value = mock_task_available_pm

        # Execute
        processor._trigger_task_available_process_model(task_available_pm_id, human_task)

        # Verify
        mock_get_process_model.assert_called_once_with(task_available_pm_id)
        mock_create_and_run.assert_called_once_with(
            mock_task_available_pm,
            persistence_level="full",
            data_to_inject={"task_guid": "task_guid_456"},
            user=process_initiator,
        )

    @patch(
        "spiffworkflow_backend.services.process_instance_processor.ProcessInstanceProcessor.setup_processor_with_process_instance"
    )
    @patch(
        "spiffworkflow_backend.services.process_instance_processor.ProcessInstanceProcessor._trigger_task_available_process_model"
    )
    @patch("spiffworkflow_backend.services.process_instance_processor.ProcessInstanceProcessor._create_new_human_task")
    @patch("spiffworkflow_backend.services.process_instance_processor.ProcessInstanceProcessor.get_potential_owners_from_task")
    @patch(
        "spiffworkflow_backend.services.process_instance_processor.ProcessInstanceProcessor._extract_task_metadata_from_extensions"
    )
    @patch(
        "spiffworkflow_backend.services.process_instance_processor.ProcessInstanceProcessor._extract_form_properties_from_extensions"
    )
    @patch("spiffworkflow_backend.services.process_instance_processor.ProcessInstanceProcessor._find_existing_human_task")
    def test_process_ready_or_waiting_task_triggers_task_available_process_model(
        self,
        mock_find_existing: MagicMock,
        mock_extract_form: MagicMock,
        mock_extract_meta: MagicMock,
        mock_get_owners: MagicMock,
        mock_create_human: MagicMock,
        mock_trigger_task_available_process_model: MagicMock,
        mock_setup: MagicMock,
        app: Flask,
    ) -> None:
        # Setup
        process_instance = ProcessInstanceModel(id=123)
        processor = ProcessInstanceProcessor(process_instance)

        ready_task = MagicMock()
        ready_task.task_spec.extensions = {"processModelToStartOnTaskAvailable": "my_task_available_model"}
        ready_task.workflow.spec.name = "process_id"

        mock_find_existing.return_value = None
        mock_extract_form.return_value = (None, None)
        mock_extract_meta.return_value = {}

        human_task = MagicMock()
        mock_create_human.return_value = human_task

        potential_owners: PotentialOwnerIdList = {"potential_owners": []}
        mock_get_owners.return_value = potential_owners

        # Execute
        processor._process_ready_or_waiting_task(ready_task, [])

        # Verify
        mock_trigger_task_available_process_model.assert_called_once_with("my_task_available_model", human_task)
