import os

from flask.app import Flask
from flask.testing import FlaskClient
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.spec_file_service import SpecFileService

from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestProcessInstancesController(BaseTest):
    def test_find_by_id(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        user_one = self.create_user_with_permission(username="user_one", target_uri="/process-instances/find-by-id/*")
        user_two = self.create_user_with_permission(username="user_two", target_uri="/process-instances/find-by-id/*")

        process_model = load_test_spec(
            process_model_id="group/sample",
            bpmn_file_name="sample.bpmn",
            process_model_source_directory="sample",
        )
        process_instance = self.create_process_instance_from_process_model(process_model=process_model, user=user_one)

        response = client.get(
            f"/v1.0/process-instances/find-by-id/{process_instance.id}",
            headers=self.logged_in_headers(user_one),
        )
        assert response.status_code == 200
        assert response.json
        assert "process_instance" in response.json
        assert response.json["process_instance"]["id"] == process_instance.id
        assert response.json["uri_type"] == "for-me"

        response = client.get(
            f"/v1.0/process-instances/find-by-id/{process_instance.id}",
            headers=self.logged_in_headers(user_two),
        )
        assert response.status_code == 400

        response = client.get(
            f"/v1.0/process-instances/find-by-id/{process_instance.id}",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200
        assert response.json
        assert "process_instance" in response.json
        assert response.json["process_instance"]["id"] == process_instance.id
        assert response.json["uri_type"] is None

    def test_process_instance_migrate(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        process_model, process_instance_id = self.create_and_run_process_instance(
            client=client,
            user=with_super_admin_user,
            process_model_id="migration-test-with-subprocess",
            bpmn_file_name="migration-initial.bpmn",
        )
        process_instance = ProcessInstanceModel.query.filter_by(id=process_instance_id).first()
        assert process_instance is not None
        processor = ProcessInstanceProcessor(process_instance)
        assert "manual_task_two" not in processor.bpmn_process_instance.spec.task_specs

        human_task_one = process_instance.active_human_tasks[0]
        assert human_task_one.task_model.task_definition.bpmn_identifier == "manual_task_one"

        new_file_path = os.path.join(
            app.instance_path,
            "..",
            "..",
            "tests",
            "data",
            "migration-test-with-subprocess",
            "migration-new.bpmn",
        )
        with open(new_file_path) as f:
            new_contents = f.read().encode()

        SpecFileService.update_file(
            process_model_info=process_model,
            file_name="migration-initial.bpmn",
            binary_data=new_contents,
            update_process_cache_only=True,
        )

        processor.suspend()
        response = client.post(
            f"/v1.0/process-instance-migrate/{self.modify_process_identifier_for_path_param(process_instance.process_model_identifier)}/{process_instance_id}",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200
        assert response.json is not None

        processor = ProcessInstanceProcessor(process_instance)
        human_task_one = process_instance.active_human_tasks[0]
        assert human_task_one.task_model.task_definition.bpmn_identifier == "manual_task_one"
        self.complete_next_manual_task(processor)

        human_task_one = process_instance.active_human_tasks[0]
        assert human_task_one.task_model.task_definition.bpmn_identifier == "manual_task_two"
        self.complete_next_manual_task(processor)

        assert process_instance.status == ProcessInstanceStatus.complete.value

    def test_process_instance_check_can_migrate(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        process_model, process_instance_id = self.create_and_run_process_instance(
            client=client,
            user=with_super_admin_user,
            process_model_id="migration-test-with-subprocess",
            bpmn_file_name="migration-initial.bpmn",
        )
        process_instance = ProcessInstanceModel.query.filter_by(id=process_instance_id).first()
        assert process_instance is not None
        processor = ProcessInstanceProcessor(process_instance)
        assert "manual_task_two" not in processor.bpmn_process_instance.spec.task_specs

        human_task_one = process_instance.active_human_tasks[0]
        assert human_task_one.task_model.task_definition.bpmn_identifier == "manual_task_one"

        new_file_path = os.path.join(
            app.instance_path,
            "..",
            "..",
            "tests",
            "data",
            "migration-test-with-subprocess",
            "migration-new.bpmn",
        )
        with open(new_file_path) as f:
            new_contents = f.read().encode()

        SpecFileService.update_file(
            process_model_info=process_model,
            file_name="migration-initial.bpmn",
            binary_data=new_contents,
            update_process_cache_only=True,
        )

        response = client.get(
            f"/v1.0/process-instances/{self.modify_process_identifier_for_path_param(process_instance.process_model_identifier)}/{process_instance_id}/check-can-migrate",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200
        assert response.json is not None
        assert response.json["can_migrate"] is True
        assert response.json["process_instance_id"] == process_instance.id
        assert response.json["current_bpmn_process_hash"] is not None

        # this can actually be None if the process model repo is not git at all
        # such as when running the docker container ci tests.
        assert "current_git_revision" in response.json
