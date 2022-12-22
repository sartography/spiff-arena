"""Test_get_localtime."""
from flask.app import Flask
from flask.testing import FlaskClient
from tests.spiffworkflow_backend.helpers.base_test import BaseTest

from spiffworkflow_backend.models.script_attributes_context import (
    ScriptAttributesContext,
)
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.scripts.add_permission import AddPermission
from spiffworkflow_backend.scripts.get_all_permissions import GetAllPermissions


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
        AddPermission().run(
            script_attributes_context, "start", "PG:hey:group", "my_test_group"
        )
        AddPermission().run(script_attributes_context, "all", "/tasks", "my_test_group")

        expected_permissions = [
            {
                "group_identifier": "my_test_group",
                "uri": "/process-instances/hey:group:%",
                "permissions": ["create"],
            },
            {
                "group_identifier": "my_test_group",
                "uri": "/process-instances/for-me/hey:group:%",
                "permissions": ["read"],
            },
            {
                "group_identifier": "my_test_group",
                "uri": "/tasks",
                "permissions": ["create", "delete", "read", "update"],
            },
        ]

        permissions = GetAllPermissions().run(script_attributes_context)
        assert permissions == expected_permissions
