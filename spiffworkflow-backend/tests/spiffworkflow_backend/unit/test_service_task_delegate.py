"""Test_various_bpmn_constructs."""
from unittest.mock import patch

import pytest
from flask.app import Flask
from tests.spiffworkflow_backend.helpers.base_test import BaseTest

from spiffworkflow_backend.services.secret_service import SecretService
from spiffworkflow_backend.services.service_task_service import ConnectorProxyError
from spiffworkflow_backend.services.service_task_service import ServiceTaskDelegate


class TestServiceTaskDelegate(BaseTest):
    """TestServiceTaskDelegate."""

    def test_check_prefixes_without_secret(
        self, app: Flask, with_db_and_bpmn_file_cleanup: None
    ) -> None:
        """Test_check_prefixes_without_secret."""
        result = ServiceTaskDelegate.check_prefixes("hey")
        assert result == "hey"

    def test_check_prefixes_with_int(
        self, app: Flask, with_db_and_bpmn_file_cleanup: None
    ) -> None:
        """Test_check_prefixes_with_int."""
        result = ServiceTaskDelegate.check_prefixes(1)
        assert result == 1

    def test_check_prefixes_with_secret(
        self, app: Flask, with_db_and_bpmn_file_cleanup: None
    ) -> None:
        """Test_check_prefixes_with_secret."""
        user = self.find_or_create_user("test_user")
        SecretService().add_secret("hot_secret", "my_secret_value", user.id)
        result = ServiceTaskDelegate.check_prefixes("secret:hot_secret")
        assert result == "my_secret_value"

    def test_invalid_call_returns_good_error_message(
        self, app: Flask, with_db_and_bpmn_file_cleanup: None
    ) -> None:
        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 404
            mock_post.return_value.ok = True
            mock_post.return_value.json.return_value = ""
            with pytest.raises(ConnectorProxyError) as ae:
                ServiceTaskDelegate.call_connector("my_invalid_operation", {}, {})
        assert "404" in str(ae)
        assert "The service did not find the requested resource." in str(ae)
        assert (
            "A critical component (The connector proxy) is not responding correctly."
            in str(ae)
        )
