import pytest
from flask.app import Flask
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.workflow_execution_service import WorkflowExecutionServiceError

from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestRefreshPermissions(BaseTest):
    def test_refresh_permissions_requires_elevated_permission(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        basic_user = self.find_or_create_user("basic_user")
        privileged_user = self.find_or_create_user("privileged_user")
        self.add_permissions_to_user(
            privileged_user,
            target_uri="/can-run-privileged-script/refresh_permissions",
            permission_names=["create"],
        )
        process_model = load_test_spec(
            process_model_id="refresh_permissions",
            process_model_source_directory="script_refresh_permissions",
        )
        process_instance = self.create_process_instance_from_process_model(process_model=process_model, user=basic_user)

        processor = ProcessInstanceProcessor(process_instance)

        with pytest.raises(WorkflowExecutionServiceError) as exception:
            processor.do_engine_steps(save=True)
            assert "ScriptUnauthorizedForUserError" in str(exception)

        process_instance = self.create_process_instance_from_process_model(process_model=process_model, user=privileged_user)
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)
        assert process_instance.status == "complete"
