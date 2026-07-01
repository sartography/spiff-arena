from unittest.mock import MagicMock
from unittest.mock import patch

from flask import current_app
from flask.app import Flask

from spiffworkflow_backend.interfaces import PotentialOwnerIdList
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.process_instance_runtime import ProcessInstanceRuntime
from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestTaskAvailableProcessModelTrigger(BaseTest):
    @patch("spiffworkflow_backend.services.process_instance_runtime.ProcessInstanceRuntime.setup_runtime_with_process_instance")
    @patch(
        "spiffworkflow_backend.background_processing.celery_tasks.process_instance_task_producer.queue_enabled_for_process_model"
    )
    def test_trigger_task_available_process_model_sends_celery_task(
        self,
        mock_queue_enabled: MagicMock,
        mock_setup: MagicMock,
        app: Flask,
    ) -> None:
        # Setup
        mock_queue_enabled.return_value = True

        process_initiator = UserModel(id=1, username="testuser", service="test", service_id="testuser")
        process_instance = ProcessInstanceModel(id=123, process_initiator=process_initiator)
        runtime = ProcessInstanceRuntime(process_instance)
        runtime.process_instance_model = process_instance

        human_task = HumanTaskModel(process_instance_id=123, task_guid="task_guid_456", task_id="task_guid_456")

        task_available_pm_id = "task_available_model"

        with patch("celery.current_app.send_task") as mock_send_task:
            runtime._trigger_task_available_process_model(task_available_pm_id, human_task.task_guid)

            from spiffworkflow_backend.background_processing import CELERY_TASK_PROCESS_INSTANCE_START_FROM_MODEL

            mock_send_task.assert_called_once_with(
                CELERY_TASK_PROCESS_INSTANCE_START_FROM_MODEL,
                (task_available_pm_id, "task_guid_456", 1),
            )

    @patch("spiffworkflow_backend.services.process_instance_runtime.ProcessInstanceRuntime.setup_runtime_with_process_instance")
    @patch(
        "spiffworkflow_backend.background_processing.celery_tasks.process_instance_task_producer.queue_enabled_for_process_model"
    )
    def test_trigger_task_available_process_model_warns_if_celery_disabled(
        self,
        mock_queue_enabled: MagicMock,
        mock_setup: MagicMock,
        app: Flask,
    ) -> None:
        # Setup
        mock_queue_enabled.return_value = False

        process_initiator = UserModel(id=1, username="testuser", service="test", service_id="testuser")
        process_instance = ProcessInstanceModel(id=123, process_initiator=process_initiator)
        runtime = ProcessInstanceRuntime(process_instance)
        runtime.process_instance_model = process_instance

        human_task = HumanTaskModel(process_instance_id=123, task_guid="task_guid_456", task_id="task_guid_456")

        task_available_pm_id = "task_available_model"

        with patch.object(current_app, "logger") as mock_logger:
            runtime._trigger_task_available_process_model(task_available_pm_id, human_task.task_guid)

            mock_logger.warning.assert_called_once_with(
                f"Cannot trigger task-available process model '{task_available_pm_id}' "
                f"for task {human_task.task_id}: Celery is not enabled."
            )

    @patch("spiffworkflow_backend.services.process_instance_runtime.ProcessInstanceRuntime.setup_runtime_with_process_instance")
    @patch("spiffworkflow_backend.services.process_instance_runtime.ProcessInstanceRuntime._trigger_task_available_process_model")
    @patch("spiffworkflow_backend.services.process_instance_runtime.ProcessInstanceRuntime._create_new_human_task")
    @patch("spiffworkflow_backend.services.process_instance_runtime.ProcessInstanceRuntime.get_potential_owners_from_task")
    @patch(
        "spiffworkflow_backend.services.process_instance_runtime.ProcessInstanceRuntime._extract_task_metadata_from_extensions"
    )
    @patch(
        "spiffworkflow_backend.services.process_instance_runtime.ProcessInstanceRuntime._extract_form_properties_from_extensions"
    )
    @patch("spiffworkflow_backend.services.process_instance_runtime.ProcessInstanceRuntime._find_existing_human_task")
    def test_process_ready_or_waiting_task_queues_task_available_process_model_trigger(
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
        runtime = ProcessInstanceRuntime(process_instance)

        ready_task = MagicMock()
        ready_task.task_spec.extensions = {"processModelToStartOnTaskAvailable": "my_task_available_model"}
        ready_task.workflow.spec.name = "process_id"

        mock_find_existing.return_value = None
        mock_extract_form.return_value = (None, None)
        mock_extract_meta.return_value = {}

        human_task = MagicMock()
        human_task.task_guid = "task_guid_456"
        mock_create_human.return_value = human_task

        potential_owners: PotentialOwnerIdList = {"potential_owners": []}
        mock_get_owners.return_value = potential_owners

        # Execute
        runtime._process_ready_or_waiting_task(ready_task, [])

        # Verify
        mock_trigger_task_available_process_model.assert_not_called()
        assert runtime._pending_task_available_process_model_triggers == [("my_task_available_model", "task_guid_456")]

    @patch("spiffworkflow_backend.services.process_instance_runtime.ProcessInstanceRuntime.setup_runtime_with_process_instance")
    def test_save_dispatches_task_available_process_model_triggers_after_commit(
        self,
        mock_setup: MagicMock,
        app: Flask,
    ) -> None:
        process_instance = ProcessInstanceModel(id=123)
        runtime = ProcessInstanceRuntime(process_instance)
        runtime.process_instance_model = process_instance
        ordered_events = []

        def queue_pending_trigger(metadata: dict) -> None:
            runtime._pending_task_available_process_model_triggers.append(("my_task_available_model", "task_guid_456"))

        def commit() -> None:
            ordered_events.append("commit")

        def trigger(task_available_process_model_identifier: str, task_guid: str) -> None:
            ordered_events.append("trigger")

        with (
            patch.object(runtime, "_save_process_instance_state"),
            patch.object(runtime, "_initialize_process_start_time_if_needed"),
            patch.object(runtime, "extract_metadata", return_value={}),
            patch.object(runtime, "_handle_process_completion"),
            patch.object(runtime, "_process_human_tasks", side_effect=queue_pending_trigger),
            patch.object(runtime, "_trigger_task_available_process_model", side_effect=trigger) as mock_trigger,
            patch.object(db.session, "add"),
            patch.object(db.session, "commit", side_effect=commit),
        ):
            runtime.save()

        assert ordered_events == ["commit", "trigger"]
        mock_trigger.assert_called_once_with("my_task_available_model", "task_guid_456")
        assert runtime._pending_task_available_process_model_triggers == []
