"""Test_logging_service."""
from flask.app import Flask
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec
from spiffworkflow_backend.services.authorization_service import AuthorizationService
from flask.testing import FlaskClient
from tests.spiffworkflow_backend.helpers.base_test import BaseTest

from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.process_instance_service import (
    ProcessInstanceService,
)
from spiffworkflow_backend.services.process_instance_processor import (
    ProcessInstanceProcessor,
)


class TestLoggingService(BaseTest):
    """Test logging service."""

    def test_logging_service_spiff_logger(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        self.create_process_group(client, with_super_admin_user, "test_group", "test_group")
        initiator_user = self.find_or_create_user("initiator_user")
        assert initiator_user.principal is not None
        AuthorizationService.import_permissions_from_yaml_file()

        process_model = load_test_spec(
            process_model_id="misc/category_number_one/simple_form",
            # bpmn_file_name="simp.bpmn",
            process_model_source_directory="simple_form",
        )
        process_instance = self.create_process_instance_from_process_model(
            process_model=process_model, user=initiator_user
        )
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)

        assert len(process_instance.active_human_tasks) == 1
        human_task = process_instance.active_human_tasks[0]
        assert len(human_task.potential_owners) == 1
        assert human_task.potential_owners[0] == initiator_user

        spiff_task = processor.__class__.get_task_by_bpmn_identifier(
            human_task.task_name, processor.bpmn_process_instance
        )
        ProcessInstanceService.complete_form_task(processor, spiff_task, {"name": "HEY"}, initiator_user, human_task)

        headers = self.logged_in_headers(with_super_admin_user)
        log_response = client.get(
            f"/v1.0/logs/{self.modify_process_identifier_for_path_param(process_model.id)}/{process_instance.id}?detailed=true",
            headers=headers,
        )
        assert log_response.status_code == 200
        assert log_response.json
        logs: list = log_response.json["results"]
        assert len(logs) == 7

        for log in logs:
            assert log["process_instance_id"] == process_instance.id
            for key in [
                "start_in_seconds",
                "end_in_seconds",
                "spiff_task_guid",
                "bpmn_process_definition_identifier",
                "task_definition_identifier",
            ]:
                assert key in log.keys()

            if log['task_definition_identifier'] == 'Activity_SimpleForm':
                assert log['username'] == initiator_user.username
