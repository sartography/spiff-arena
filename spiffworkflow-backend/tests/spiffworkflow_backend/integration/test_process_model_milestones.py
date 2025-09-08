from flask.app import Flask
from starlette.testclient import TestClient

from spiffworkflow_backend.models.user import UserModel
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestProcessModelMilestones(BaseTest):
    def test_process_model_milestone_list(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        process_model = load_test_spec(
            "test_group/test-last-milestone",
            process_model_source_directory="test-last-milestone",
        )

        headers = self.logged_in_headers(with_super_admin_user)
        modified_process_model_id = process_model.modified_process_model_identifier()
        response = client.get(f"/v1.0/process-models/{modified_process_model_id}/milestones", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "milestones" in data
        milestones = data["milestones"]
        assert len(milestones) == 3

        start_milestone = milestones[0]
        assert start_milestone is not None
        assert start_milestone["name"] == "Start"
        assert start_milestone["file"] == "test_last_milestone_call_activity.bpmn"
        assert start_milestone["task_type"] == "StartEvent"

        intermediate_milestone = milestones[1]
        assert intermediate_milestone is not None
        assert intermediate_milestone["name"] == "In Call Activity"
        assert intermediate_milestone["task_type"] == "IntermediateThrowEvent"

        end_milestone = milestones[2]
        assert end_milestone is not None
        assert end_milestone["name"] == "Done with call activity"
        assert end_milestone["task_type"] == "EndEvent"
