import json

from flask.app import Flask
from flask.testing import FlaskClient
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.routes.tasks_controller import _dequeued_interstitial_stream
from spiffworkflow_backend.services.authorization_service import AuthorizationService
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor

from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestTasksController(BaseTest):
    def test_task_show(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        process_group_id = "my_process_group"
        process_model_id = "dynamic_enum_select_fields"
        bpmn_file_location = "dynamic_enum_select_fields"
        process_model = self.create_group_and_model_with_bpmn(
            client,
            with_super_admin_user,
            process_group_id=process_group_id,
            process_model_id=process_model_id,
            # bpmn_file_name=bpmn_file_name,
            bpmn_file_location=bpmn_file_location,
        )

        headers = self.logged_in_headers(with_super_admin_user)
        response = self.create_process_instance_from_process_model_id_with_api(client, process_model.id, headers)
        assert response.json is not None
        process_instance_id = response.json["id"]

        response = client.post(
            f"/v1.0/process-instances/{self.modify_process_identifier_for_path_param(process_model.id)}/{process_instance_id}/run",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        # Call this to assure all engine-steps are fully processed.
        _dequeued_interstitial_stream(process_instance_id)
        assert response.json is not None
        assert response.json["next_task"] is not None

        human_tasks = (
            db.session.query(HumanTaskModel).filter(HumanTaskModel.process_instance_id == process_instance_id).all()
        )
        assert len(human_tasks) == 1
        human_task = human_tasks[0]
        response = client.get(
            f"/v1.0/tasks/{process_instance_id}/{human_task.task_id}",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200
        assert response.json is not None
        assert response.json["form_schema"]["definitions"]["Color"]["anyOf"][1]["title"] == "Green"

        # if you set this in task data:
        #   form_ui_hidden_fields = ["veryImportantFieldButOnlySometimes", "building.floor"]
        # you will get this ui schema:
        assert response.json["form_ui_schema"] == {
            "building": {"floor": {"ui:widget": "hidden"}},
            "veryImportantFieldButOnlySometimes": {"ui:widget": "hidden"},
        }

    def test_interstitial_page(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        process_group_id = "my_process_group"
        process_model_id = "interstitial"
        bpmn_file_location = "interstitial"
        # Assure we have someone in the finance team
        finance_user = self.find_or_create_user("testuser2")
        AuthorizationService.import_permissions_from_yaml_file()
        process_model = self.create_group_and_model_with_bpmn(
            client,
            with_super_admin_user,
            process_group_id=process_group_id,
            process_model_id=process_model_id,
            bpmn_file_location=bpmn_file_location,
        )
        headers = self.logged_in_headers(with_super_admin_user)
        response = self.create_process_instance_from_process_model_id_with_api(client, process_model.id, headers)
        assert response.json is not None
        process_instance_id = response.json["id"]

        response = client.post(
            f"/v1.0/process-instances/{self.modify_process_identifier_for_path_param(process_model.id)}/{process_instance_id}/run",
            headers=headers,
        )

        assert response.json is not None
        assert response.json["next_task"] is not None
        assert response.json["next_task"]["state"] == "READY"
        assert response.json["next_task"]["title"] == "Script Task #2"

        # Rather that call the API and deal with the Server Side Events, call the loop directly and covert it to
        # a list.  It tests all of our code.  No reason to test Flasks SSE support.
        stream_results = _dequeued_interstitial_stream(process_instance_id)
        results = list(stream_results)
        # strip the "data:" prefix and convert remaining string to dict.
        json_results = [json.loads(x[5:]) for x in results]  # type: ignore
        # There should be 2 results back -
        # the first script task should not be returned (it contains no end user instructions)
        # The second script task should produce rendered jinja text
        # The Manual Task should then return a message as well.
        assert len(results) == 2
        assert json_results[0]["task"]["state"] == "READY"
        assert json_results[0]["task"]["title"] == "Script Task #2"
        assert json_results[0]["task"]["properties"]["instructionsForEndUser"] == "I am Script Task 2"
        assert json_results[1]["task"]["state"] == "READY"
        assert json_results[1]["task"]["title"] == "Manual Task"

        response = client.put(
            f"/v1.0/tasks/{process_instance_id}/{json_results[1]['task']['id']}",
            headers=headers,
        )

        assert response.json is not None

        # we should now be on a task that does not belong to the original user, and the interstitial page should know this.
        results = list(_dequeued_interstitial_stream(process_instance_id))
        json_results = [json.loads(x[5:]) for x in results]  # type: ignore
        assert len(results) == 1
        assert json_results[0]["task"]["state"] == "READY"
        assert json_results[0]["task"]["can_complete"] is False
        assert json_results[0]["task"]["title"] == "Please Approve"
        assert json_results[0]["task"]["properties"]["instructionsForEndUser"] == "I am a manual task in another lane"

        # Suspending the task should still report that the user can not complete the task.
        process_instance = ProcessInstanceModel.query.filter_by(id=process_instance_id).first()
        processor = ProcessInstanceProcessor(process_instance)
        processor.suspend()
        processor.save()

        results = list(_dequeued_interstitial_stream(process_instance_id))
        json_results = [json.loads(x[5:]) for x in results]  # type: ignore
        assert len(results) == 1
        assert json_results[0]["task"]["state"] == "READY"
        assert json_results[0]["task"]["can_complete"] is False
        assert json_results[0]["task"]["title"] == "Please Approve"
        assert json_results[0]["task"]["properties"]["instructionsForEndUser"] == "I am a manual task in another lane"

        # Complete task as the finance user.
        response = client.put(
            f"/v1.0/tasks/{process_instance_id}/{json_results[0]['task']['id']}",
            headers=self.logged_in_headers(finance_user),
        )

        # We should now be on the end task with a valid message, even after loading it many times.
        list(_dequeued_interstitial_stream(process_instance_id))
        list(_dequeued_interstitial_stream(process_instance_id))
        results = list(_dequeued_interstitial_stream(process_instance_id))
        json_results = [json.loads(x[5:]) for x in results]  # type: ignore
        assert len(json_results) == 1
        assert json_results[0]["task"]["state"] == "COMPLETED"
        assert json_results[0]["task"]["properties"]["instructionsForEndUser"] == "I am the end task"

    def test_correct_user_can_get_and_update_a_task(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        initiator_user = self.find_or_create_user("testuser4")
        finance_user = self.find_or_create_user("testuser2")
        assert initiator_user.principal is not None
        assert finance_user.principal is not None
        AuthorizationService.import_permissions_from_yaml_file()

        finance_group = GroupModel.query.filter_by(identifier="Finance Team").first()
        assert finance_group is not None

        process_group_id = "finance"
        process_model_id = "model_with_lanes"
        bpmn_file_name = "lanes.bpmn"
        bpmn_file_location = "model_with_lanes"
        process_model = self.create_group_and_model_with_bpmn(
            client,
            with_super_admin_user,
            process_group_id=process_group_id,
            process_model_id=process_model_id,
            bpmn_file_name=bpmn_file_name,
            bpmn_file_location=bpmn_file_location,
        )

        response = self.create_process_instance_from_process_model_id_with_api(
            client,
            process_model.id,
            headers=self.logged_in_headers(initiator_user),
        )
        assert response.status_code == 201

        assert response.json is not None
        process_instance_id = response.json["id"]
        response = client.post(
            f"/v1.0/process-instances/{self.modify_process_identifier_for_path_param(process_model.id)}/{process_instance_id}/run",
            headers=self.logged_in_headers(initiator_user),
        )
        assert response.status_code == 200

        response = client.get(
            "/v1.0/tasks",
            headers=self.logged_in_headers(finance_user),
        )
        assert response.status_code == 200
        assert response.json is not None
        assert len(response.json["results"]) == 0

        response = client.get(
            "/v1.0/tasks",
            headers=self.logged_in_headers(initiator_user),
        )
        assert response.status_code == 200
        assert response.json is not None
        assert len(response.json["results"]) == 1

        task_id = response.json["results"][0]["id"]
        assert task_id is not None

        response = client.put(
            f"/v1.0/tasks/{process_instance_id}/{task_id}",
            headers=self.logged_in_headers(finance_user),
        )
        assert response.status_code == 500
        assert response.json
        assert "UserDoesNotHaveAccessToTaskError" in response.json["message"]

        response = client.put(
            f"/v1.0/tasks/{process_instance_id}/{task_id}",
            headers=self.logged_in_headers(initiator_user),
        )
        assert response.status_code == 200

        response = client.get(
            "/v1.0/tasks",
            headers=self.logged_in_headers(initiator_user),
        )
        assert response.status_code == 200
        assert response.json is not None
        assert len(response.json["results"]) == 0

        response = client.get(
            "/v1.0/tasks",
            headers=self.logged_in_headers(finance_user),
        )
        assert response.status_code == 200
        assert response.json is not None
        assert len(response.json["results"]) == 1

    def test_task_save_draft(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        process_group_id = "test_group"
        process_model_id = "simple_form"
        process_model = self.create_group_and_model_with_bpmn(
            client,
            with_super_admin_user,
            process_group_id=process_group_id,
            process_model_id=process_model_id,
        )

        response = self.create_process_instance_from_process_model_id_with_api(
            client,
            process_model.id,
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 201

        assert response.json is not None
        process_instance_id = response.json["id"]
        response = client.post(
            f"/v1.0/process-instances/{self.modify_process_identifier_for_path_param(process_model.id)}/{process_instance_id}/run",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200

        response = client.get(
            "/v1.0/tasks",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200
        assert response.json is not None
        assert len(response.json["results"]) == 1

        task_id = response.json["results"][0]["id"]
        assert task_id is not None

        draft_data = {"HEY": "I'm draft"}

        response = client.post(
            f"/v1.0/tasks/{process_instance_id}/{task_id}/save-draft",
            headers=self.logged_in_headers(with_super_admin_user),
            content_type="application/json",
            data=json.dumps(draft_data),
        )
        assert response.status_code == 200

        response = client.get(
            f"/v1.0/tasks/{process_instance_id}/{task_id}",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200
        assert response.json is not None
        assert response.json["saved_form_data"] == draft_data

        response = client.put(
            f"/v1.0/tasks/{process_instance_id}/{task_id}",
            headers=self.logged_in_headers(with_super_admin_user),
            content_type="application/json",
            data=json.dumps(draft_data),
        )
        assert response.status_code == 200

        # ensure draft data is deleted after submitting the task
        response = client.get(
            f"/v1.0/tasks/{process_instance_id}/{task_id}",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200
        assert response.json is not None
        assert response.json["saved_form_data"] is None
        assert response.json["data"]["HEY"] == draft_data["HEY"]
