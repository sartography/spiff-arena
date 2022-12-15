"""Test_get_localtime."""
from flask.app import Flask
from flask.testing import FlaskClient
from flask_bpmn.models.db import db

from spiffworkflow_backend.models.permission_target import PermissionTargetModel
from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
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


class TestDeletePermissions(BaseTest):
    """TestGetGroupMembers."""

    def test_can_delete_members (
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_can_get_members_of_a_group."""
        initiator_user = self.find_or_create_user("initiator_user")
        testuser1 = self.find_or_create_user("testuser1")
        testuser2 = self.find_or_create_user("testuser2")
        testuser3 = self.find_or_create_user("testuser3")
        group_a = GroupService.find_or_create_group('groupA')
        group_b = GroupService.find_or_create_group('groupB')
        db.session.add(group_a)
        db.session.add(group_b)
        db.session.commit()
        UserService.add_user_to_group(testuser1, group_a)
        UserService.add_user_to_group(testuser2, group_a)
        UserService.add_user_to_group(testuser3, group_b)

        target = PermissionTargetModel('test/*')
        db.session.add(target)
        db.session.commit()
        AuthorizationService.create_permission_for_principal(group_a.principal,
                                                             target,
                                                             "read")
        # now that we have everything, try to clear it out...
        script_attributes_context = ScriptAttributesContext(
            task=None,
            environment_identifier="testing",
            process_instance_id=1,
            process_model_identifier="my_test_user",
        )
        result = ClearPermissions().run(
            script_attributes_context
        )

        groups = GroupModel.query.all()
        assert(0 == len(groups))
