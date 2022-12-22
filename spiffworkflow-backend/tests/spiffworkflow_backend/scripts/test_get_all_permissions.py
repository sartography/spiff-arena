"""Test_get_localtime."""
import pytest
from flask.app import Flask
from flask.testing import FlaskClient
from flask_bpmn.api.api_error import ApiError
from spiffworkflow_backend.scripts.get_all_permissions import GetAllPermissions
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec

from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.permission_assignment import PermissionAssignmentModel
from spiffworkflow_backend.models.permission_target import PermissionTargetModel
from spiffworkflow_backend.models.script_attributes_context import (
    ScriptAttributesContext,
)
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.scripts.add_permission import AddPermission
from spiffworkflow_backend.services.process_instance_processor import (
    ProcessInstanceProcessor,
)


class TestGetAllPermissions(BaseTest):

    def test_can_get_all_permissions(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
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
        AddPermission().run(
            script_attributes_context, "all", "/tasks", "my_test_group"
        )

        expected_permissions = [
            {'group_identifier': 'my_test_group', 'uri': '/process-instances/hey:group:%', 'permissions': ['create']},
            {'group_identifier': 'my_test_group', 'uri': '/process-instances/for-me/hey:group:%', 'permissions': ['read']},
            {'group_identifier': 'my_test_group', 'uri': '/tasks', 'permissions': ['create', 'delete', 'read', 'update']}
        ]

        permissions = GetAllPermissions().run(script_attributes_context)
        assert permissions == expected_permissions
