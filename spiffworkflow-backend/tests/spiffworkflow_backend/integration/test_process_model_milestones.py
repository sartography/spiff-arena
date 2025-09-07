from unittest.mock import MagicMock
from unittest.mock import patch

from flask.app import Flask
from starlette.testclient import TestClient

from spiffworkflow_backend.models.file import FileType
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.models.user import UserModel
from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestProcessModelMilestones(BaseTest):
    def test_process_model_milestone_list(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test the process_model_milestone_list endpoint."""
        # Create a mock process model
        process_model_id = "test_group/test_model"
        process_model = ProcessModelInfo(
            id=process_model_id,
            display_name="Test Model",
            description="A test model",
        )

        # Create a mock BPMN file with some milestones
        bpmn_content = b"""<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL">
  <bpmn:process id="Process_1">
    <bpmn:startEvent id="StartEvent_1" name="Start">
      <bpmn:outgoing>Flow_1</bpmn:outgoing>
    </bpmn:startEvent>
    <bpmn:sequenceFlow id="Flow_1" sourceRef="StartEvent_1" targetRef="Task_1" />
    <bpmn:task id="Task_1" name="Task 1">
      <bpmn:incoming>Flow_1</bpmn:incoming>
      <bpmn:outgoing>Flow_2</bpmn:outgoing>
    </bpmn:task>
    <bpmn:sequenceFlow id="Flow_2" sourceRef="Task_1" targetRef="IntermediateThrowEvent_1" />
    <bpmn:intermediateThrowEvent id="IntermediateThrowEvent_1" name="Ready for approvals">
      <bpmn:incoming>Flow_2</bpmn:incoming>
      <bpmn:outgoing>Flow_3</bpmn:outgoing>
    </bpmn:intermediateThrowEvent>
    <bpmn:sequenceFlow id="Flow_3" sourceRef="IntermediateThrowEvent_1" targetRef="Task_2" />
    <bpmn:task id="Task_2" name="Task 2">
      <bpmn:incoming>Flow_3</bpmn:incoming>
      <bpmn:outgoing>Flow_4</bpmn:outgoing>
    </bpmn:task>
    <bpmn:sequenceFlow id="Flow_4" sourceRef="Task_2" targetRef="EndEvent_1" />
    <bpmn:endEvent id="EndEvent_1" name="End">
      <bpmn:incoming>Flow_4</bpmn:incoming>
    </bpmn:endEvent>
  </bpmn:process>
</bpmn:definitions>"""

        # Mock the necessary functions for the endpoint
        with (
            patch("spiffworkflow_backend.routes.process_models_controller._get_process_model") as mock_get_process_model,
            patch(
                "spiffworkflow_backend.services.process_model_service.ProcessModelService.get_process_model_files"
            ) as mock_get_files,
            patch("spiffworkflow_backend.services.spec_file_service.SpecFileService.get_data") as mock_get_data,
            patch("spiffworkflow_backend.services.workflow_spec_service.WorkflowSpecService.get_spec") as mock_get_spec,
        ):
            # Configure the mocks
            mock_get_process_model.return_value = process_model

            # Mock file
            mock_file = MagicMock()
            mock_file.type = FileType.bpmn.value
            mock_file.name = "test.bpmn"
            mock_get_files.return_value = [mock_file]

            mock_get_data.return_value = bpmn_content
            mock_get_spec.return_value = None

            # Call the endpoint
            headers = self.logged_in_headers(with_super_admin_user)
            modified_process_model_id = process_model_id.replace("/", ":")
            response = client.get(f"/v1.0/process-models/{modified_process_model_id}/milestones", headers=headers)

            # Verify the response
            assert response.status_code == 200
            data = response.json()

            # Check that the response contains milestones
            assert "milestones" in data
            milestones = data["milestones"]

            # Verify the expected milestones
            assert len(milestones) == 3

            # Verify exact milestone names in order (start events, then intermediate events, then end events)
            milestone_names = [m["name"] for m in milestones]
            assert milestone_names == ["Start", "Ready for approvals", "End"]

            # Find and verify the StartEvent milestone
            start_milestone = next((m for m in milestones if m["bpmn_identifier"] == "StartEvent_1"), None)
            assert start_milestone is not None
            assert start_milestone["name"] == "Start"
            assert start_milestone["task_type"] == "StartEvent"

            # Find and verify the IntermediateThrowEvent milestone
            intermediate_milestone = next((m for m in milestones if m["bpmn_identifier"] == "IntermediateThrowEvent_1"), None)
            assert intermediate_milestone is not None
            assert intermediate_milestone["name"] == "Ready for approvals"
            assert intermediate_milestone["task_type"] == "IntermediateThrowEvent"

            # Find and verify the EndEvent milestone
            end_milestone = next((m for m in milestones if m["bpmn_identifier"] == "EndEvent_1"), None)
            assert end_milestone is not None
            assert end_milestone["name"] == "End"
            assert end_milestone["task_type"] == "EndEvent"
