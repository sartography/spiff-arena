"""Test_get_localtime."""
from operator import itemgetter

from flask.app import Flask
from flask.testing import FlaskClient
from tests.spiffworkflow_backend.helpers.base_test import BaseTest

from spiffworkflow_backend.models.script_attributes_context import (
    ScriptAttributesContext,
)
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.scripts.get_all_permissions import GetAllPermissions
from spiffworkflow_backend.services.authorization_service import AuthorizationService


class TestGetAllPermissions(BaseTest):
    """TestGetAllPermissions."""

    def test_can_get_all_permissions(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_can_get_all_permissions."""
        self.find_or_create_user("test_user")

        # now that we have everything, try to clear it out...
        script_attributes_context = ScriptAttributesContext(
            task=None,
            environment_identifier="testing",
            process_instance_id=1,
            process_model_identifier="my_test_user",
        )
        AuthorizationService.add_permission_from_uri_or_macro(
            permission="start", target="PG:hey:group", group_identifier="my_test_group"
        )
        AuthorizationService.add_permission_from_uri_or_macro(
            permission="all", target="/tasks", group_identifier="my_test_group"
        )

        expected_permissions = [
            {
                "group_identifier": "my_test_group",
                "uri": "/process-instances/hey:group:*",
                "permissions": ["create"],
            },
            {
                "group_identifier": "my_test_group",
                "uri": "/process-instances/for-me/hey:group:*",
                "permissions": ["read"],
            },
            {
                "group_identifier": "my_test_group",
                "uri": "/tasks",
                "permissions": ["create", "read", "update", "delete"],
            },
        ]

        permissions = GetAllPermissions().run(script_attributes_context)
        sorted_permissions = sorted(permissions, key=itemgetter("uri"))
        sorted_expected_permissions = sorted(
            expected_permissions, key=itemgetter("uri")
        )
        assert sorted_permissions == sorted_expected_permissions
