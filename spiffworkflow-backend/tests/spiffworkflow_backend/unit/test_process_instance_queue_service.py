"""Test_process_instance_queue_service."""
from flask.app import Flask
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.services.process_instance_queue_service import (
    ProcessInstanceQueueService,
)


class TestProcessInstanceQueueService(BaseTest):
    """TestProcessInstanceQueueService."""

    def test_newly_created_process_instances_are_added_to_the_queue(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        initiator_user = self.find_or_create_user("initiator_user")
        process_model = load_test_spec(
            process_model_id="test_group/model_with_lanes",
            bpmn_file_name="lanes.bpmn",
            process_model_source_directory="model_with_lanes",
        )
        process_instance = self.create_process_instance_from_process_model(
            process_model=process_model, user=initiator_user
        )
        not_started_ids = ProcessInstanceQueueService.peek_many("not_started")
        assert process_instance.id in not_started_ids
