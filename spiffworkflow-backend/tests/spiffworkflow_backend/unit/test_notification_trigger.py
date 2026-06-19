from unittest.mock import MagicMock
from unittest.mock import patch

from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestNotificationTrigger(BaseTest):
    @patch(
        "spiffworkflow_backend.services.process_instance_processor.ProcessInstanceProcessor.setup_processor_with_process_instance"
    )
    @patch("spiffworkflow_backend.services.process_instance_service.ProcessInstanceService.create_and_run_process_instance")
    @patch("spiffworkflow_backend.services.process_model_service.ProcessModelService.get_process_model")
    @patch("spiffworkflow_backend.models.db.db.session")
    def test_trigger_notification_process_model_with_user(
        self, mock_session, mock_get_process_model, mock_create_and_run, mock_setup, app
    ):
        # Setup
        process_instance = ProcessInstanceModel(id=123)
        processor = ProcessInstanceProcessor(process_instance)

        human_task = HumanTaskModel(process_instance_id=123, task_id="task_guid_456")

        potential_owner_user = UserModel(id=789, username="testuser", email="test@example.com")
        mock_session.get.side_effect = lambda model, id: potential_owner_user if model == UserModel and id == 789 else None

        potential_owner_hash = {"potential_owners": [{"user_id": 789}]}

        notification_pm_id = "notification_model"
        mock_notification_pm = MagicMock()
        mock_get_process_model.return_value = mock_notification_pm

        app.config["SPIFFWORKFLOW_BACKEND_URL_FOR_FRONTEND"] = "http://frontend"

        # Execute
        processor._trigger_notification_process_model(notification_pm_id, human_task, potential_owner_hash)

        # Verify
        mock_get_process_model.assert_called_once_with(notification_pm_id)

        expected_data = {
            "task_url": "http://frontend/tasks/123/task_guid_456",
            "process_instance_id": 123,
            "task_guid": "task_guid_456",
            "api_path": "/tasks/123/task_guid_456",
            "frontend_url": "http://frontend",
            "potential_owners": [{"type": "user", "user": potential_owner_user.as_dict()}],
            "potential_groups": [],
            "lane_owner_usernames_waiting": [],
        }

        mock_create_and_run.assert_called_once_with(mock_notification_pm, persistence_level="full", data_to_inject=expected_data)

    @patch(
        "spiffworkflow_backend.services.process_instance_processor.ProcessInstanceProcessor.setup_processor_with_process_instance"
    )
    @patch("spiffworkflow_backend.services.process_instance_service.ProcessInstanceService.create_and_run_process_instance")
    @patch("spiffworkflow_backend.services.process_model_service.ProcessModelService.get_process_model")
    @patch("spiffworkflow_backend.models.db.db.session")
    def test_trigger_notification_process_model_with_group(
        self, mock_session, mock_get_process_model, mock_create_and_run, mock_setup, app
    ):
        # Setup
        process_instance = ProcessInstanceModel(id=123)
        processor = ProcessInstanceProcessor(process_instance)

        human_task = HumanTaskModel(process_instance_id=123, task_id="task_guid_456")

        potential_owner_group = GroupModel(id=999, identifier="testgroup")
        mock_session.get.side_effect = lambda model, id: potential_owner_group if model == GroupModel and id == 999 else None

        potential_owner_hash = {
            "potential_owners": [],
            "lane_owner_group_ids": [999],
            "lane_owner_usernames_waiting": ["waiting@example.com"],
        }

        notification_pm_id = "notification_model"
        mock_notification_pm = MagicMock()
        mock_get_process_model.return_value = mock_notification_pm

        app.config["SPIFFWORKFLOW_BACKEND_URL_FOR_FRONTEND"] = "http://frontend"

        # Execute
        processor._trigger_notification_process_model(notification_pm_id, human_task, potential_owner_hash)

        # Verify
        expected_data = {
            "task_url": "http://frontend/tasks/123/task_guid_456",
            "process_instance_id": 123,
            "task_guid": "task_guid_456",
            "api_path": "/tasks/123/task_guid_456",
            "frontend_url": "http://frontend",
            "potential_owners": [],
            "potential_groups": [{"id": 999, "identifier": "testgroup"}],
            "lane_owner_usernames_waiting": ["waiting@example.com"],
        }

        mock_create_and_run.assert_called_once_with(mock_notification_pm, persistence_level="full", data_to_inject=expected_data)

    @patch(
        "spiffworkflow_backend.services.process_instance_processor.ProcessInstanceProcessor.setup_processor_with_process_instance"
    )
    @patch(
        "spiffworkflow_backend.services.process_instance_processor.ProcessInstanceProcessor._trigger_notification_process_model"
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
    def test_process_ready_or_waiting_task_triggers_notification(
        self,
        mock_find_existing,
        mock_extract_form,
        mock_extract_meta,
        mock_get_owners,
        mock_create_human,
        mock_trigger_notification,
        mock_setup,
        app,
    ):
        # Setup
        process_instance = ProcessInstanceModel(id=123)
        processor = ProcessInstanceProcessor(process_instance)

        ready_task = MagicMock()
        ready_task.task_spec.extensions = {"properties": {"notificationProcessModel": "my_notification_model"}}
        ready_task.workflow.spec.name = "process_id"

        mock_find_existing.return_value = None
        mock_extract_form.return_value = (None, None)
        mock_extract_meta.return_value = {}

        human_task = MagicMock()
        mock_create_human.return_value = human_task

        potential_owners = {"potential_owners": []}
        mock_get_owners.return_value = potential_owners

        # Execute
        processor._process_ready_or_waiting_task(ready_task, [])

        # Verify
        mock_trigger_notification.assert_called_once_with("my_notification_model", human_task, potential_owners)
