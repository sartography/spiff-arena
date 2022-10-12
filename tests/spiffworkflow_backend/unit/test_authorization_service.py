"""Test_message_service."""
import pytest
from flask import Flask
from tests.spiffworkflow_backend.helpers.base_test import BaseTest

from spiffworkflow_backend.models.user import UserNotFoundError
from spiffworkflow_backend.services.authorization_service import AuthorizationService


class TestAuthorizationService(BaseTest):
    """TestAuthorizationService."""

    def test_can_raise_if_missing_user(
        self, app: Flask, with_db_and_bpmn_file_cleanup: None
    ) -> None:
        """Test_can_raise_if_missing_user."""
        with pytest.raises(UserNotFoundError):
            AuthorizationService.import_permissions_from_yaml_file(
                raise_if_missing_user=True
            )

    def test_can_import_permissions_from_yaml(
        self, app: Flask, with_db_and_bpmn_file_cleanup: None
    ) -> None:
        """Test_can_import_permissions_from_yaml."""
        usernames = [
            "testadmin1",
            "testadmin2",
            "testuser1",
            "testuser2",
            "testuser3",
            "testuser4",
        ]
        users = {}
        for username in usernames:
            user = self.find_or_create_user(username=username)
            users[username] = user

        AuthorizationService.import_permissions_from_yaml_file()
        assert len(users["testadmin1"].groups) == 1
        assert users["testadmin1"].groups[0].identifier == "admin"
        assert len(users["testuser1"].groups) == 1
        assert users["testuser1"].groups[0].identifier == "finance"
        assert len(users["testuser2"].groups) == 2

        self.assert_user_has_permission(
            users["testuser1"], "update", "/v1.0/process-groups/finance/model1"
        )
        self.assert_user_has_permission(
            users["testuser1"], "update", "/v1.0/process-groups/finance/"
        )
        self.assert_user_has_permission(
            users["testuser1"], "update", "/v1.0/process-groups/", expected_result=False
        )
        self.assert_user_has_permission(
            users["testuser4"], "update", "/v1.0/process-groups/finance/model1"
        )
        self.assert_user_has_permission(
            users["testuser4"], "read", "/v1.0/process-groups/finance/model1"
        )
        self.assert_user_has_permission(
            users["testuser2"], "update", "/v1.0/process-groups/finance/model1"
        )
        self.assert_user_has_permission(
            users["testuser2"], "update", "/v1.0/process-groups/", expected_result=False
        )
        self.assert_user_has_permission(
            users["testuser2"], "read", "/v1.0/process-groups/"
        )
