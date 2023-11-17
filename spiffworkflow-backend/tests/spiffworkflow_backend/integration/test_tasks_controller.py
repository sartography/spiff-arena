import json

from flask.app import Flask
from flask.testing import FlaskClient
from spiffworkflow_backend.models.bpmn_process_definition import BpmnProcessDefinitionModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
from spiffworkflow_backend.models.task import TaskModel
from spiffworkflow_backend.models.task_definition import TaskDefinitionModel
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
        assert response.status_code == 200
        # Call this to assure all engine-steps are fully processed.
        _dequeued_interstitial_stream(process_instance_id)

        human_tasks = (
            db.session.query(HumanTaskModel).filter(HumanTaskModel.process_instance_id == process_instance_id).all()
        )

        {
            r.bpmn_identifier
            for r in db.session.query(BpmnProcessDefinitionModel.bpmn_identifier)  # type: ignore
            .join(TaskDefinitionModel)
            .join(TaskModel)
            .filter(TaskModel.process_instance_id == process_instance_id)
            .filter(TaskModel.state == "READY")
            .distinct()
        }

        assert len(human_tasks) == 1
        human_task = human_tasks[0]
        response = client.get(
            f"/v1.0/tasks/{process_instance_id}/{human_task.task_id}?with_form_data=true",
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

    def test_prepare_schema(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        task_data = {
            "title": "Title injected with jinja syntax",
            "foods": [
                {"value": "apples", "label": "apples"},
                {"value": "oranges", "label": "oranges"},
                {"value": "bananas", "label": "bananas"},
            ],
            "form_ui_hidden_fields": ["DontShowMe"],
        }
        form_schema = {
            "title": "{{title}}",
            "type": "object",
            "properties": {
                "favoriteFood": {
                    "type": "string",
                    "title": "Favorite Food",
                    "anyOf": ["options_from_task_data_var:foods"],
                },
                "DontShowMe": {
                    "type": "string",
                    "title": "Don't Show Me",
                },
            },
        }
        form_ui: dict = {}

        data = {"form_schema": form_schema, "form_ui": form_ui, "task_data": task_data}

        self.logged_in_headers(with_super_admin_user)
        response = client.post(
            "/v1.0/tasks/prepare-form",
            headers=self.logged_in_headers(with_super_admin_user),
            data=json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json is not None
        assert response.json["form_schema"]["properties"]["favoriteFood"]["anyOf"] == [
            {"enum": ["apples"], "title": "apples", "type": "string"},
            {"enum": ["oranges"], "title": "oranges", "type": "string"},
            {"enum": ["bananas"], "title": "bananas", "type": "string"},
        ]
        assert response.json["form_schema"]["title"] == task_data["title"]
        assert response.json["form_ui"] == {"DontShowMe": {"ui:widget": "hidden"}}

    def test_interstitial_returns_process_instance_if_suspended_or_terminated(
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
        assert process_instance_id

        process_instance = ProcessInstanceModel.query.filter_by(id=process_instance_id).first()
        assert process_instance is not None

        process_instance.status = ProcessInstanceStatus.suspended.value
        db.session.add(process_instance)
        db.session.commit()
        stream_results = _dequeued_interstitial_stream(process_instance.id)
        results = list(stream_results)
        json_results = [json.loads(x[5:]) for x in results]  # type: ignore
        assert len(json_results) == 1
        assert json_results[0]["type"] == "unrunnable_instance"
        assert json_results[0]["unrunnable_instance"]["id"] == process_instance.id
        assert json_results[0]["unrunnable_instance"]["status"] == "suspended"

        process_instance.status = ProcessInstanceStatus.terminated.value
        db.session.add(process_instance)
        db.session.commit()
        stream_results = _dequeued_interstitial_stream(process_instance.id)
        results = list(stream_results)
        json_results = [json.loads(x[5:]) for x in results]  # type: ignore
        assert len(json_results) == 1
        assert json_results[0]["type"] == "unrunnable_instance"
        assert json_results[0]["unrunnable_instance"]["id"] == process_instance.id
        assert json_results[0]["unrunnable_instance"]["status"] == "terminated"

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
        assert response.status_code == 200

        task_model = TaskModel.query.filter_by(process_instance_id=process_instance_id, state="READY").first()
        assert task_model is not None
        assert task_model.task_definition.bpmn_name == "Script Task #2"

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
            f"/v1.0/tasks/{process_instance_id}/{json_results[1]['task']['id']}?with_form_data=true",
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
            f"/v1.0/tasks/{process_instance_id}/{json_results[0]['task']['id']}?with_form_data=true",
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
            f"/v1.0/tasks/{process_instance_id}/{task_id}?with_form_data=true",
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
            f"/v1.0/tasks/{process_instance_id}/{task_id}?with_form_data=true",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200
        assert response.json is not None
        assert response.json["saved_form_data"] is None
        assert response.json["data"]["HEY"] == draft_data["HEY"]

    def test_can_complete_complete_a_guest_task(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        process_group_id = "my_process_group"
        process_model_id = "test-allow-guest"
        bpmn_file_location = "test-allow-guest"
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
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200

        task_model = TaskModel.query.filter_by(process_instance_id=process_instance_id, state="READY").first()
        assert task_model is not None
        task_guid = task_model.guid

        # log in a guest user to complete the tasks
        redirect_url = "/test-redirect-dne"
        response = client.get(
            f"/v1.0/login?process_instance_id={process_instance_id}&task_guid={task_guid}&redirect_url={redirect_url}&authentication_identifier=DOES_NOT_MATTER",
        )
        assert response.status_code == 302
        assert response.location == redirect_url
        headers_dict = dict(response.headers)
        assert "Set-Cookie" in headers_dict
        cookie = headers_dict["Set-Cookie"]
        access_token = cookie.split(";")[0].split("=")[1]
        assert access_token is not None

        # ensure guest user can get and complete both guest manual tasks
        response = client.get(
            f"/v1.0/tasks/{process_instance_id}/{task_guid}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        response = client.put(
            f"/v1.0/tasks/{process_instance_id}/{task_guid}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        assert response.json is not None
        task_guid = response.json["id"]
        assert task_guid is not None
        response = client.put(
            f"/v1.0/tasks/{process_instance_id}/{task_guid}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        assert response.json is not None
        assert "guest_confirmation" in response.json

        # ensure user gets logged out when they try to go anywhere else
        response = client.get(
            "/v1.0/tasks",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 403
        headers_dict = dict(response.headers)
        assert "Set-Cookie" in headers_dict
        cookie = headers_dict["Set-Cookie"]
        access_token = cookie.split(";")[0].split("=")[1]
        assert access_token == ""
