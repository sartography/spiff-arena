import json
import threading
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

from flask import Flask
from flask import g
from starlette.testclient import TestClient

from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.task import TaskModel
from spiffworkflow_backend.models.task_definition import TaskDefinitionModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.message_service import MessageService
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestLongRunningService(BaseTest):
    def assert_tasks_awaiting_callback(
        self,
        app: Flask,
        client: TestClient,
        user: UserModel,
        expected_count: int,
    ) -> None:
        task_models = (
            TaskModel.query.join(TaskDefinitionModel)
            .join(ProcessInstanceModel)
            .filter(
                TaskModel.state == "STARTED",
                TaskDefinitionModel.typename == "ServiceTask",
                ProcessInstanceModel.process_initiator_id == user.id,
                ProcessInstanceModel.status == "waiting",
            )
            .all()
        )
        assert len(task_models) == expected_count
        for task_model in task_models:
            assert task_model.guid is not None
            assert task_model.process_instance_id is not None
            assert task_model.task_definition.bpmn_name or task_model.task_definition.bpmn_identifier
            assert task_model.process_instance.process_model_identifier is not None

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
            spiff__task_id = json_data["spiff__task_id"]
            processor.save()

        # One task should be awaiting callback
        self.assert_tasks_awaiting_callback(app, client, with_super_admin_user, 1)

        # Execute the callback url to complete the process
        content = {
            "command_response": {
                "body": {"do_not_fail": True},
                "mimetype": "application/json",
            },
            "command_response_version": 2,
            "error": None,
        }
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

        # logging information should be properly collected
        headers = self.logged_in_headers(with_super_admin_user)
        log_response = client.get(
            f"/v1.0/logs/{self.modify_process_identifier_for_path_param(process_model.id)}/{process_instance.id}?events=true",
            headers=headers,
        )
        assert log_response.status_code == 200
        logs = log_response.json()
        assert logs

        service_task_logs = [log for log in logs["results"] if log["bpmn_task_type"] == "ServiceTask"]
        assert len(service_task_logs) == 1
        assert service_task_logs[0]["event_type"] == "task_completed"
        assert service_task_logs[0]["username"] == with_super_admin_user.username

        # The task in the database should be marked as completed
        task_model = TaskModel.query.filter_by(guid=spiff__task_id).first()
        assert task_model is not None
        assert task_model.state == "COMPLETED"

    def test__202_callback_url_uses_public_backend_base(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        process_model_id = "test_group/service_task"
        process_model = load_test_spec(
            process_model_id=process_model_id,
            process_model_source_directory="service_task",
        )

        with (
            self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_URL", "https://backend.example.com/api"),
            self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_URL_FOR_FRONTEND", "https://frontend.example.com"),
            self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_API_PATH_PREFIX", "/api/v1.0"),
        ):
            with app.test_request_context():
                process_instance = self.create_process_instance_from_process_model(process_model, user=with_super_admin_user)
                processor = ProcessInstanceProcessor(process_instance)
                with patch("requests.post") as mock_post:
                    mock_post.return_value.status_code = 202
                    mock_post.return_value.ok = True
                    mock_post.return_value.text = json.dumps({})
                    processor.do_engine_steps(save=True)
                callback_url = mock_post.call_args.kwargs["json"]["spiff__callback_url"]
                spiff_task_id = mock_post.call_args.kwargs["json"]["spiff__task_id"]

        assert callback_url == f"https://backend.example.com/api/v1.0/tasks/{process_instance.id}/{spiff_task_id}/callback"

    def test__message_started_202_service_task_accepts_immediate_callback(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """A callback can arrive while a message-started instance is still inside its initial service task."""
        process_model_id = "test_group/message_start_service_task"
        load_test_spec(
            process_model_id=process_model_id,
            process_model_source_directory="message_start_service_task",
        )

        callback_can_retry = threading.Event()
        callback_finished = threading.Event()
        callback_waiting_on_lock = threading.Event()
        callback_result: dict[str, Any] = {}
        callback_thread: threading.Thread | None = None
        content = {
            "command_response": {
                "body": {"do_not_fail": True},
                "mimetype": "application/json",
            },
            "command_response_version": 2,
            "error": None,
        }
        callback_headers = self.logged_in_headers(with_super_admin_user, {"mimetype": "application/json"})

        def submit_callback(callback_url: str) -> None:
            try:
                callback_result["response"] = client.put(
                    callback_url,
                    headers=callback_headers,
                    json=content,
                )
            finally:
                callback_finished.set()

        def mock_connector_post(*_args: object, **kwargs: Any) -> SimpleNamespace:
            nonlocal callback_thread
            json_data = kwargs.get("json", {})
            assert isinstance(json_data, dict)
            callback_url = json_data["spiff__callback_url"]
            assert isinstance(callback_url, str)
            callback_thread = threading.Thread(target=submit_callback, args=(callback_url,))
            callback_thread.start()
            while not callback_finished.is_set() and not callback_waiting_on_lock.is_set():
                callback_finished.wait(timeout=0.01)
            return SimpleNamespace(status_code=202, ok=True, text=json.dumps({}), headers={})

        def wait_for_message_run_to_finish(_seconds: int) -> None:
            callback_waiting_on_lock.set()
            callback_can_retry.wait(timeout=5)

        g.user = with_super_admin_user
        with (
            patch("requests.post", side_effect=mock_connector_post),
            patch("spiffworkflow_backend.services.process_instance_queue_service.time.sleep", wait_for_message_run_to_finish),
        ):
            try:
                receiver_message = MessageService.run_process_model_from_message("test_group:quick_callback_service_task", {})
            finally:
                callback_can_retry.set()

        assert callback_thread is not None
        callback_thread.join(timeout=5)
        assert not callback_thread.is_alive()

        response = callback_result["response"]
        assert response.status_code == 200
        assert response.json()["type"] == "Default End Event"

        process_instance = ProcessInstanceService().get_process_instance(receiver_message.process_instance_id)
        assert process_instance.status == "complete"

    def test__parallel_202_service_task_accepts_immediate_callback(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """A callback can arrive before a parallel branch has finished the same engine run."""
        process_model_id = "test_group/parallel_service_task_callback"
        process_model = load_test_spec(
            process_model_id=process_model_id,
            process_model_source_directory="parallel_service_task_callback",
        )

        callback_finished = threading.Event()
        callback_result: dict[str, Any] = {}
        callback_thread: threading.Thread | None = None
        content = {
            "command_response": {
                "body": {"do_not_fail": True},
                "mimetype": "application/json",
            },
            "command_response_version": 2,
            "error": None,
        }
        callback_headers = self.logged_in_headers(with_super_admin_user, {"mimetype": "application/json"})

        def submit_callback(callback_url: str) -> None:
            try:
                callback_result["response"] = client.put(
                    callback_url,
                    headers=callback_headers,
                    json=content,
                )
            finally:
                callback_finished.set()

        def mock_connector_post(*_args: object, **kwargs: Any) -> SimpleNamespace:
            nonlocal callback_thread
            json_data = kwargs.get("json", {})
            assert isinstance(json_data, dict)
            callback_url = json_data["spiff__callback_url"]
            assert isinstance(callback_url, str)
            callback_thread = threading.Thread(target=submit_callback, args=(callback_url,))
            callback_thread.start()
            return SimpleNamespace(status_code=202, ok=True, text=json.dumps({}), headers={})

        with app.test_request_context():
            process_instance = self.create_process_instance_from_process_model(process_model, user=with_super_admin_user)
            processor = ProcessInstanceProcessor(process_instance)
            with patch("requests.post", side_effect=mock_connector_post):
                processor.do_engine_steps(save=True)

        assert callback_thread is not None
        callback_thread.join(timeout=5)
        assert not callback_thread.is_alive()

        response = callback_result["response"]
        assert response.status_code == 200
        assert response.json()["type"] == "Default End Event"

        process_instance = ProcessInstanceService().get_process_instance(process_instance.id)
        assert process_instance.status == "complete"

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
        content = {
            "command_response": {
                "body": {"some_other_key": True},
                "mimetype": "application/json",
            },
            "command_response_version": 2,
            "error": None,
        }
        response = client.put(
            callback_url,
            headers=self.logged_in_headers(with_super_admin_user, {"mimetype": "application/json"}),
            json=content,
        )
        response_dict = response.json()
        assert response.status_code == 400
        assert response_dict["title"] == "unexpected_workflow_exception"
        process_instance = ProcessInstanceService().get_process_instance(process_instance.id)
        assert process_instance.status == "error"

        # The process instance is in a state of error, which should mean the task is no longer waiting.
        self.assert_tasks_awaiting_callback(app, client, with_super_admin_user, 0)

    def test__202_connector_error_response(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """When a callback provides connector-style error data, it should follow normal service-task error handling."""
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

        content = {
            "error": {
                "error_code": "OurTestError",
                "message": "We errored",
            },
            "command_response": {
                "body": "{}",
                "mimetype": "application/json",
            },
            "command_response_version": 2,
        }
        response = client.put(
            callback_url, headers=self.logged_in_headers(with_super_admin_user, {"mimetype": "application/json"}), json=content
        )
        response_dict = response.json()
        assert response.status_code == 400
        assert response_dict["title"] == "unexpected_workflow_exception"

        process_instance = ProcessInstanceService().get_process_instance(process_instance.id)
        assert process_instance.status == "error"
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
        assert process_instance.status == "complete"  # sending the cancel event will move the process to a completed state.

        # No task should be awaiting callback
        self.assert_tasks_awaiting_callback(app, client, with_super_admin_user, 0)

        # Execute the callback, which should fail with a 400, because it received a cancel signal event, and moved on.
        content = {
            "command_response": {
                "body": {"do_not_fail": True},
                "mimetype": "application/json",
            },
            "command_response_version": 2,
            "error": None,
        }
        response = client.put(
            callback_url, headers=self.logged_in_headers(with_super_admin_user, {"mimetype": "application/json"}), json=content
        )
        assert response.status_code == 400
        response_dict = response.json()
        assert response_dict["title"] == "not_waiting_for_callback"
        process_instance = ProcessInstanceService().get_process_instance(process_instance.id)
        assert process_instance.status == "complete"  # The process should not be in an error state.

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
        content = {
            "command_response": {
                "body": {"do_not_fail": True},
                "mimetype": "application/json",
            },
            "command_response_version": 2,
            "error": None,
        }

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
