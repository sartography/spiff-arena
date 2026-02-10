import json
from unittest.mock import patch

from flask import Flask
from starlette.testclient import TestClient

from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec

# To Do:
# 1) Test Connector Request
#    * Assure con Provide an API endpoint and a new UI component that lnector gets process in
#      stance id, the task id, the callback url. (done)
# 2) Test Post Request
#    * Test built-in function that provides a callback url (done)
# 3) General Test
#    * Assure that a 202 request results in the process being in a waiting state. (done)
#    * Assure that a call to the call-back url results in the process completing. (done)
# 4) Error handling
#    * If the process is successfully able to complete all engine steps, a 200 message should be returned (done)
#    * If an error occurs completing engine steps, a 400 error should be returned for the call-back, and
#      the process should be in an error state. (done)
#    * If the task is no longer waiting, we receive an error, but the process is not placed in an error state. (done)
# 5) Reporting
#    * Provide an API endpoint and a new UI component that lists all processes that are waiting on a callback. (done)
# 6) Invalid callbacks should not put the process in an error state.  Assure this is true. (done)
# 7) Test execution mode flag is respected. (done)
# 8) Assure someone without permissions can not call the url (done)
# 9) After implementation
#    * Click test to assure the process does not compete in the ui
#    * Be sure to add documentation on all of this


class TestLongRunningService(BaseTest):
    def assert_tasks_awaiting_callback(
        self,
        app: Flask,
        client: TestClient,
        user: UserModel,
        expected_count: int,
    ) -> None:
        """Call the tasks/awaiting-callback endpoint and assert the expected number of tasks are returned."""
        response = client.get(
            "/v1.0/tasks/awaiting-callback",
            headers=self.logged_in_headers(user),
        )
        assert response.status_code == 200
        response_json = response.json()
        assert response_json["pagination"]["total"] == expected_count
        assert len(response_json["results"]) == expected_count

    def test_connector_receives_additional_metadata(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        process_model_id = "test_group/service_task"
        process_model = load_test_spec(
            process_model_id=process_model_id,
            process_model_source_directory="service_task",
        )
        with app.test_request_context():
            process_instance = self.create_process_instance_from_process_model(process_model)
            processor = ProcessInstanceProcessor(process_instance)
            connector_response = {"do_not_fail": True}
            with patch("requests.post") as mock_post:
                mock_post.return_value.status_code = 200
                mock_post.return_value.ok = True
                mock_post.return_value.text = json.dumps(connector_response)
                processor.do_engine_steps(save=True)

            # Verify that the POST request includes required metadata
            assert mock_post.called, "mock_post should have been called"
            call_kwargs = mock_post.call_args.kwargs
            json_data = call_kwargs.get("json", {})
            assert "spiff__process_instance_id" in json_data, "process_instance_id should exist in POST data"
            assert "spiff__task_id" in json_data, "task_id should exist in POST data"
            assert "spiff__callback_url" in json_data, "callback_url should exist in POST data"
            assert json_data["spiff__process_instance_id"] == process_instance.id

            # If it is not a successful 200 (and not a 202) the the process should be fully completed without any
            # additional call.
            assert process_instance.status == "complete"

            # No tasks should be awaiting a call back.
            self.assert_tasks_awaiting_callback(app, client, with_super_admin_user, 0)

    def test__202_success_response(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        process_model_id = "test_group/service_task"
        process_model = load_test_spec(
            process_model_id=process_model_id,
            process_model_source_directory="service_task",
        )

        with app.test_request_context():
            process_instance = self.create_process_instance_from_process_model(process_model, user=with_super_admin_user)
            processor = ProcessInstanceProcessor(process_instance)
            with patch("requests.post") as mock_post:
                mock_post.return_value.status_code = 202
                mock_post.return_value.ok = True
                mock_post.return_value.text = json.dumps({})
                processor.do_engine_steps(save=True)
            assert process_instance.status == "waiting"
            call_kwargs = mock_post.call_args.kwargs
            json_data = call_kwargs.get("json", {})
            callback_url = json_data["spiff__callback_url"]
            processor.save()

        # One task should be awaiting callback
        self.assert_tasks_awaiting_callback(app, client, with_super_admin_user, 1)

        # Execute the callback url to complete the process
        content = {"do_not_fail": True}
        response = client.put(
            callback_url, headers=self.logged_in_headers(with_super_admin_user, {"mimetype": "application/json"}), json=content
        )
        assert response.status_code == 200
        response_dict = response.json()
        assert response_dict["state"] == "COMPLETED"
        assert response_dict["type"] == "Default End Event"

        process_instance = ProcessInstanceService().get_process_instance(process_instance.id)
        assert process_instance.status == "complete"

        # No tasks should be awaiting callback
        self.assert_tasks_awaiting_callback(app, client, with_super_admin_user, 0)

    def test__202_error_response(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """When a callback provides data that causes a subsequent task to fail, the process should go to error state."""
        process_model_id = "test_group/service_task"
        process_model = load_test_spec(
            process_model_id=process_model_id,
            process_model_source_directory="service_task",
        )

        with app.test_request_context():
            process_instance = self.create_process_instance_from_process_model(process_model, user=with_super_admin_user)
            processor = ProcessInstanceProcessor(process_instance)
            with patch("requests.post") as mock_post:
                mock_post.return_value.status_code = 202
                mock_post.return_value.ok = True
                mock_post.return_value.text = json.dumps({})
                processor.do_engine_steps(save=True)
            assert process_instance.status == "waiting"
            call_kwargs = mock_post.call_args.kwargs
            json_data = call_kwargs.get("json", {})
            callback_url = json_data["spiff__callback_url"]

        # One task should be awaiting callback
        self.assert_tasks_awaiting_callback(app, client, with_super_admin_user, 1)

        # Execute the callback WITHOUT "do_not_fail" - the script task after the service task
        # will raise a KeyError, which should put the process in an error state.
        content = {"some_other_key": True}
        response = client.put(
            callback_url, headers=self.logged_in_headers(with_super_admin_user, {"mimetype": "application/json"}), json=content
        )
        response_dict = response.json()
        assert response.status_code == 400
        assert response_dict["title"] == "unexpected_workflow_exception"
        process_instance = ProcessInstanceService().get_process_instance(process_instance.id)
        assert process_instance.status == "error"

        # The process instance is in a state of error, which should mean the task is no longer waiting.
        self.assert_tasks_awaiting_callback(app, client, with_super_admin_user, 0)

    def test__202_canceled_response(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """When the service task that would receive a callback is no longer active, we return an error message and the
        process is not modified."""
        process_model_id = "test_group/service_task"
        process_model = load_test_spec(
            process_model_id=process_model_id,
            process_model_source_directory="service_task",
        )

        with app.test_request_context():
            process_instance = self.create_process_instance_from_process_model(process_model, user=with_super_admin_user)
            processor = ProcessInstanceProcessor(process_instance)
            with patch("requests.post") as mock_post:
                mock_post.return_value.status_code = 202
                mock_post.return_value.ok = True
                mock_post.return_value.text = json.dumps({})
                processor.do_engine_steps(save=True)
            assert process_instance.status == "waiting"
            call_kwargs = mock_post.call_args.kwargs
            json_data = call_kwargs.get("json", {})
            callback_url = json_data["spiff__callback_url"]

        # One task should be awaiting callback
        self.assert_tasks_awaiting_callback(app, client, with_super_admin_user, 1)

        processor.send_bpmn_event(
            {"name": "CANCEL", "typename": "SignalEventDefinition", "variable": None, "expression": None, "description": None}
        )
        assert process_instance.status == "complete"

        # No task should be awaiting callback
        self.assert_tasks_awaiting_callback(app, client, with_super_admin_user, 0)

        # Execute the callback, which should not be completed, because it received a canel signal event.
        content = {"do_not_fail": True}
        response = client.put(
            callback_url, headers=self.logged_in_headers(with_super_admin_user, {"mimetype": "application/json"}), json=content
        )
        assert response.status_code == 400
        response_dict = response.json()
        assert response_dict["title"] == "not_waiting_for_callback"
        process_instance = ProcessInstanceService().get_process_instance(process_instance.id)
        assert process_instance.status == "complete"  # It should not be changed to an error, it should remain completed.

    def test__202_permissions(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Assure that when a different user makes the call it is not accepted."""
        process_model_id = "test_group/service_task"
        process_model = load_test_spec(
            process_model_id=process_model_id,
            process_model_source_directory="service_task",
        )

        with app.test_request_context():
            process_instance = self.create_process_instance_from_process_model(process_model, user=with_super_admin_user)
            processor = ProcessInstanceProcessor(process_instance)
            with patch("requests.post") as mock_post:
                mock_post.return_value.status_code = 202
                mock_post.return_value.ok = True
                mock_post.return_value.text = json.dumps({})
                processor.do_engine_steps(save=True)
            assert process_instance.status == "waiting"
            call_kwargs = mock_post.call_args.kwargs
            json_data = call_kwargs.get("json", {})
            callback_url = json_data["spiff__callback_url"]

        self.assert_tasks_awaiting_callback(app, client, with_super_admin_user, 1)
        content = {"do_not_fail": True}

        # Execute the callback, as a different user
        user = self.find_or_create_user("joe")
        response = client.put(callback_url, headers=self.logged_in_headers(user, {"mimetype": "application/json"}), json=content)
        assert response.status_code == 403
        response_dict = response.json()
        assert response_dict["title"] == "not_authorized"

        # Execute the callback, without any authentication
        response = client.put(callback_url, headers={"mimetype": "application/json"}, json=content)
        assert response.status_code == 403
        response_dict = response.json()
        assert response_dict["title"] == "not_authorized"

        process_instance = ProcessInstanceService().get_process_instance(process_instance.id)
        assert process_instance.status == "waiting"  # It should not be changed to an error, it should remain completed.
