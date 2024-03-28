from flask.app import Flask
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
from spiffworkflow_backend.services.authorization_service import AuthorizationService
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService

from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestGetUrlForTaskWithBpmnIdentifier(BaseTest):
    def test_get_url_for_task_works(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        initiator_user = self.find_or_create_user("initiator_user")
        assert initiator_user.principal is not None
        AuthorizationService.import_permissions_from_yaml_file()

        process_model = load_test_spec(
            process_model_id="misc/test-get-url-for-task-with-bpmn-identifier",
            process_model_source_directory="test-get-url-for-task-with-bpmn-identifier",
            bpmn_file_name="test-get-url-for-task-with-bpmn-identifier.bpmn",
        )
        process_instance = self.create_process_instance_from_process_model(process_model=process_model, user=initiator_user)
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)

        assert len(process_instance.active_human_tasks) == 1
        human_task = process_instance.active_human_tasks[0]
        assert len(human_task.potential_owners) == 1
        assert human_task.potential_owners[0] == initiator_user

        spiff_task = processor.__class__.get_task_by_bpmn_identifier(human_task.task_name, processor.bpmn_process_instance)
        ProcessInstanceService.complete_form_task(processor, spiff_task, {}, initiator_user, human_task)
        assert process_instance.status == ProcessInstanceStatus.complete.value
        assert spiff_task is not None
        assert "url" in spiff_task.data

        fe_url = app.config["SPIFFWORKFLOW_BACKEND_URL_FOR_FRONTEND"]
        expected_url = f"{fe_url}/public/tasks/{process_instance.id}/{str(spiff_task.id)}"
        assert spiff_task.data["url"] == expected_url

    def test_get_url_for_task_can_get_non_public_url(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        initiator_user = self.find_or_create_user("initiator_user")
        assert initiator_user.principal is not None
        AuthorizationService.import_permissions_from_yaml_file()

        process_model = load_test_spec(
            process_model_id="misc/test-get-url-for-task-with-bpmn-identifier",
            process_model_source_directory="test-get-url-for-task-with-bpmn-identifier",
            bpmn_file_name="test-get-url-for-task-with-bpmn-identifier-non-public.bpmn",
        )
        process_instance = self.create_process_instance_from_process_model(process_model=process_model, user=initiator_user)
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)

        assert len(process_instance.active_human_tasks) == 1
        human_task = process_instance.active_human_tasks[0]
        assert len(human_task.potential_owners) == 1
        assert human_task.potential_owners[0] == initiator_user

        spiff_task = processor.__class__.get_task_by_bpmn_identifier(human_task.task_name, processor.bpmn_process_instance)
        ProcessInstanceService.complete_form_task(processor, spiff_task, {}, initiator_user, human_task)
        assert process_instance.status == ProcessInstanceStatus.complete.value
        assert spiff_task is not None
        assert "url" in spiff_task.data

        fe_url = app.config["SPIFFWORKFLOW_BACKEND_URL_FOR_FRONTEND"]
        expected_url = f"{fe_url}/tasks/{process_instance.id}/{str(spiff_task.id)}"
        assert spiff_task.data["url"] == expected_url
