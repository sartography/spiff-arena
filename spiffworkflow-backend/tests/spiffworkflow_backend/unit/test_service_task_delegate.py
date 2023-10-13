from unittest.mock import patch

import pytest
from flask.app import Flask
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.secret_service import SecretService
from spiffworkflow_backend.services.service_task_service import ConnectorProxyError
from spiffworkflow_backend.services.service_task_service import ServiceTaskDelegate

from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestServiceTaskDelegate(BaseTest):
    def test_check_prefixes_without_secret(self, app: Flask, with_db_and_bpmn_file_cleanup: None) -> None:
        result = ServiceTaskDelegate.value_with_secrets_replaced("hey")
        assert result == "hey"

    def test_check_prefixes_with_int(self, app: Flask, with_db_and_bpmn_file_cleanup: None) -> None:
        result = ServiceTaskDelegate.value_with_secrets_replaced(1)
        assert result == 1

    def test_check_prefixes_with_secret(self, app: Flask, with_db_and_bpmn_file_cleanup: None) -> None:
        user = self.find_or_create_user("test_user")
        SecretService().add_secret("hot_secret", "my_secret_value", user.id)
        result = ServiceTaskDelegate.value_with_secrets_replaced("secret:hot_secret")
        assert result == "my_secret_value"

    def test_check_prefixes_with_spiff_secret(self, app: Flask, with_db_and_bpmn_file_cleanup: None) -> None:
        user = self.find_or_create_user("test_user")
        SecretService().add_secret("hot_secret", "my_secret_value", user.id)
        result = ServiceTaskDelegate.value_with_secrets_replaced("TOKEN SPIFF_SECRET:hot_secret-haha")
        assert result == "TOKEN my_secret_value-haha"

    def test_check_prefixes_with_spiff_secret_in_dict(self, app: Flask, with_db_and_bpmn_file_cleanup: None) -> None:
        user = self.find_or_create_user("test_user")
        SecretService().add_secret("hot_secret", "my_secret_value", user.id)
        result = ServiceTaskDelegate.value_with_secrets_replaced(
            {"Authorization": "TOKEN SPIFF_SECRET:hot_secret-haha"}
        )
        assert result == {"Authorization": "TOKEN my_secret_value-haha"}

    def test_invalid_call_returns_good_error_message(self, app: Flask, with_db_and_bpmn_file_cleanup: None) -> None:
        process_model = load_test_spec(
            process_model_id="test_group/model_with_lanes",
            bpmn_file_name="lanes.bpmn",
            process_model_source_directory="model_with_lanes",
        )
        process_instance = self.create_process_instance_from_process_model(process_model=process_model)
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)
        spiff_task = processor.next_task()

        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 404
            mock_post.return_value.ok = True
            mock_post.return_value.json.return_value = ""
            with pytest.raises(ConnectorProxyError) as ae:
                ServiceTaskDelegate.call_connector("my_invalid_operation", {}, spiff_task)
        assert "404" in str(ae)
        assert "The service did not find the requested resource." in str(ae)
        assert "A critical component (The connector proxy) is not responding correctly." in str(ae)
