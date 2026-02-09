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
#    * Test built-in function that provides a callback url
# 3) General Test
#    * Assure that a 202 request results in the process being in a waiting state.
#    * Assure that a call to the call-back url results in the process completing.
# 4) Error handling
#    * If the process is successfully able to complete all engine steps, a 200 message should be returned
#    * If an error occurs completing engine steps, a 500 error should be returned for the call-back
#    * If a timeout occurs (a timer event cancels the call back, then we return an error message that
#       the task is no longer active.
# 5) Reporting
#    * Provide an API endpoint and a new UI component that lists all processes that are waiting on a callback.
# 6) After implementation
#    * Click test to assure the process does not compete in the ui
#    * Be sure to add documentation on all of this
# 7) Invalid callbacks should not put the process in an error state.  Assure this is true.
# 8) Test execution mode flag is respected.
# 9) Assure someone without permissions can not call the url


class TestLongRunningService(BaseTest):
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
            assert process_instance.status == "complete"

    def test__202_response(
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

        # Execute the callback url to complete the process
        content = {"do_not_fail": True}
        client.put(
            callback_url, headers=self.logged_in_headers(with_super_admin_user, {"mimetype": "application/json"}), json=content
        )
        process_instance = ProcessInstanceService().get_process_instance(process_instance.id)
        assert process_instance.status == "complete"

        # Now post to callback url to complete the process
