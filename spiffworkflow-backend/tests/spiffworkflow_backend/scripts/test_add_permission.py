"""Test_get_localtime."""
from flask.app import Flask
from flask.testing import FlaskClient
from flask_bpmn.models.db import db

from spiffworkflow_backend.models.permission_assignment import PermissionAssignmentModel
from spiffworkflow_backend.models.permission_target import PermissionTargetModel
from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.add_permission import AddPermission
from spiffworkflow_backend.scripts.clear_permissions import ClearPermissions
from spiffworkflow_backend.services.authorization_service import AuthorizationService
from spiffworkflow_backend.services.group_service import GroupService
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec

from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.process_instance_processor import (
    ProcessInstanceProcessor,
)
from spiffworkflow_backend.services.user_service import UserService


class TestAddPermission(BaseTest):
    """TestAddPermission."""

    def test_can_add_permission (
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_can_get_members_of_a_group."""
        test_user = self.find_or_create_user("test_user")

        # now that we have everything, try to clear it out...
        script_attributes_context = ScriptAttributesContext(
            task=None,
            environment_identifier="testing",
            process_instance_id=1,
            process_model_identifier="my_test_user",
        )

        group = GroupModel.query.filter(GroupModel.identifier == 'my_test_group').first()
        permission_target = PermissionTargetModel.query.filter(PermissionTargetModel.uri == '/test_add_permission/%').first()
        assert(group is None)
        assert(permission_target is None)

        result = AddPermission().run(
            script_attributes_context,
            "read",
            "/test_add_permission/*",
            "my_test_group"
        )
        group = GroupModel.query.filter(GroupModel.identifier == 'my_test_group').first()
        permission_target = PermissionTargetModel.query.filter(PermissionTargetModel.uri == '/test_add_permission/%').first()
        permission_assignments = PermissionAssignmentModel.query.filter(PermissionAssignmentModel.principal_id == group.principal.id).all()
        assert(group is not None)
        assert(permission_target is not None)
        assert(len(permission_assignments) == 1)
