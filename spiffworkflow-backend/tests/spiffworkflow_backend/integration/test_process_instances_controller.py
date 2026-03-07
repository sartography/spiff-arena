import os

from flask.app import Flask
from starlette.testclient import TestClient

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.spec_file_service import SpecFileService
from spiffworkflow_backend.services.workflow_storage_service import WorkflowStorageService
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestProcessInstancesController(BaseTest):
    def test_task_info_to_task_guid_excludes_unfinished_tasks_in_blob_mode(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        user = self.create_user_with_permission("super_admin")
        process_model = self.create_group_and_model_with_bpmn(
            client,
            user,
            process_group_id="test_group",
            process_model_id="step_through_gateway",
        )
        response = self.create_process_instance_from_process_model_id_with_api(
            client,
            process_model.id,
            headers=self.logged_in_headers(user),
        )
        assert response.status_code == 201
        assert response.json() is not None
        process_instance_id = int(response.json()["id"])
        response = client.post(
            f"/v1.0/process-instances/{self.modify_process_identifier_for_path_param(process_model.id)}/{process_instance_id}/run",
            headers=self.logged_in_headers(user),
        )
        assert response.status_code == 200

        process_instance = ProcessInstanceModel.query.filter_by(id=process_instance_id).first()
        assert process_instance is not None
        processor = ProcessInstanceProcessor(process_instance)
        self.complete_next_manual_task(processor)
        processor.save()

        process_instance = ProcessInstanceModel.query.filter_by(id=process_instance_id).first()
        assert process_instance is not None
        processor = ProcessInstanceProcessor(
            process_instance,
            include_task_data_for_completed_tasks=True,
            include_completed_subprocesses=True,
        )
        WorkflowStorageService.save_workflow(process_instance, processor.serialize())
        process_instance.workflow_storage_strategy = WorkflowStorageService.BLOB_BASED
        db.session.add(process_instance)
        db.session.commit()

        response = client.get(
            (
                f"/v1.0/process-instances/{self.modify_process_identifier_for_path_param(process_model.id)}"
                f"/{process_instance_id}/task-info?most_recent_tasks_only=true"
            ),
            headers=self.logged_in_headers(user),
        )
        assert response.status_code == 200
        assert response.json() is not None
        task_list = response.json()
        target_task = next((task for task in task_list if task["state"] in ["COMPLETED", "ERROR"]), None)
        assert target_task is not None

        unfinished_guids = [
            task["guid"] for task in task_list if task["end_in_seconds"] is None and task["guid"] != target_task["guid"]
        ]
        assert len(unfinished_guids) > 0

        response = client.get(
            (
                f"/v1.0/process-instances/{self.modify_process_identifier_for_path_param(process_model.id)}"
                f"/{process_instance_id}/task-info?most_recent_tasks_only=true&to_task_guid={target_task['guid']}"
            ),
            headers=self.logged_in_headers(user),
        )
        assert response.status_code == 200
        assert response.json() is not None
        historical_task_guids = {task["guid"] for task in response.json()}
        for unfinished_guid in unfinished_guids:
            assert unfinished_guid not in historical_task_guids

    def test_find_by_id(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        user_one = self.create_user_with_permission(username="user_one", target_uri="/process-instances/find-by-id/*")
        user_two = self.create_user_with_permission(username="user_two", target_uri="/process-instances/find-by-id/*")

        process_model = load_test_spec(
            process_model_id="group/sample",
            process_model_source_directory="sample",
        )
        process_instance = self.create_process_instance_from_process_model(process_model=process_model, user=user_one)

        response = client.get(
            f"/v1.0/process-instances/find-by-id/{process_instance.id}",
            headers=self.logged_in_headers(user_one),
        )
        assert response.status_code == 200
        assert response.json()
        assert "process_instance" in response.json()
        assert response.json()["process_instance"]["id"] == process_instance.id
        assert response.json()["uri_type"] == "for-me"

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
        assert response.json()
        assert "process_instance" in response.json()
        assert response.json()["process_instance"]["id"] == process_instance.id
        assert response.json()["uri_type"] is None

    def test_process_instance_migrate(
        self,
        app: Flask,
        client: TestClient,
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
        assert response.json() is not None

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
        client: TestClient,
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
        assert response.json() is not None
        assert response.json()["can_migrate"] is True
        assert response.json()["process_instance_id"] == process_instance.id
        assert response.json()["current_bpmn_process_hash"] is not None

        # this can actually be None if the process model repo is not git at all
        # such as when running the docker container ci tests.
        assert "current_git_revision" in response.json()

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

        assert None not in milestone_names
        assert "" not in milestone_names
