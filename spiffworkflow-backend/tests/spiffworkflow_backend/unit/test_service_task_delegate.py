"""Test_various_bpmn_constructs."""
from flask.app import Flask
from spiffworkflow_backend.services.secret_service import SecretService
from spiffworkflow_backend.services.service_task_service import ServiceTaskDelegate
from tests.spiffworkflow_backend.helpers.base_test import BaseTest


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
