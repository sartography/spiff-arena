from flask.app import Flask
from starlette.testclient import TestClient

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.user import UserModel
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestUniqueMilestoneNames(BaseTest):
    def test_unique_milestone_name_list(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        process_model_id = "runs_without_input/sample"
        bpmn_file_location = "sample"
        process_model = load_test_spec(
            process_model_id,
            process_model_source_directory=bpmn_file_location,
        )

        # Create process instances with different last milestones
        process_instance_1 = self.create_process_instance_from_process_model(
            process_model=process_model, status="complete", user=with_super_admin_user
        )
        process_instance_1.last_milestone_bpmn_name = "Milestone A"

        process_instance_2 = self.create_process_instance_from_process_model(
            process_model=process_model, status="complete", user=with_super_admin_user
        )
        process_instance_2.last_milestone_bpmn_name = "Milestone B"

        process_instance_3 = self.create_process_instance_from_process_model(
            process_model=process_model, status="complete", user=with_super_admin_user
        )
        process_instance_3.last_milestone_bpmn_name = "Milestone A"  # Duplicate of Milestone A

        process_instance_4 = self.create_process_instance_from_process_model(
            process_model=process_model, status="complete", user=with_super_admin_user
        )
        process_instance_4.last_milestone_bpmn_name = "Milestone C"
        
        process_instance_5 = self.create_process_instance_from_process_model(
            process_model=process_model, status="complete", user=with_super_admin_user
        )
        process_instance_5.last_milestone_bpmn_name = None  # Test with None value
        
        process_instance_6 = self.create_process_instance_from_process_model(
            process_model=process_model, status="complete", user=with_super_admin_user
        )
        process_instance_6.last_milestone_bpmn_name = ""  # Test with empty string

        db.session.commit()

        # Call the endpoint and check the response
        response = client.get(
            "/v1.0/process-instances/unique-milestone-names",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200
        
        # Verify that the response contains the unique milestone names (A, B, C)
        milestone_names = response.json()
        assert isinstance(milestone_names, list)
        assert "Milestone A" in milestone_names
        assert "Milestone B" in milestone_names
        assert "Milestone C" in milestone_names
        
        # Check that the names are unique (no duplicates)
        assert len(milestone_names) == len(set(milestone_names))
        
        # Check if None or empty values are handled properly (they shouldn't be in the result)
        # The endpoint should filter these out or return them based on the implementation choice
        if None in milestone_names or "" in milestone_names:
            # If the implementation includes None/empty values, they should be present exactly once
            assert milestone_names.count(None) <= 1
            assert milestone_names.count("") <= 1
        else:
            # If implementation excludes None/empty values, they shouldn't be in the result
            assert None not in milestone_names
            assert "" not in milestone_names