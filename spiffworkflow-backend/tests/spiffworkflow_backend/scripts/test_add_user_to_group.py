"""Test_get_localtime."""
from flask.app import Flask
from flask.testing import FlaskClient
from flask_bpmn.models.db import db

from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.models.user_group_assignment_waiting import UserGroupAssignmentWaitingModel
from spiffworkflow_backend.scripts.add_user_to_group import AddUserToGroup
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec

from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.process_instance_processor import (
    ProcessInstanceProcessor,
)
from spiffworkflow_backend.services.user_service import UserService


class TestAddUserToGroup(BaseTest):
    """TestGetGroupMembers."""

    def test_can_add_existing_user_to_existing_group(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_can_get_members_of_a_group."""
        my_user = self.find_or_create_user("my_user")
        my_group = GroupModel(identifier="my_group")
        db.session.add(my_group)
        script_attributes_context = ScriptAttributesContext(
            task=None,
            environment_identifier="testing",
            process_instance_id=1,
            process_model_identifier="my_test_user",
        )
        result = AddUserToGroup().run(
            script_attributes_context,
            my_user.username,
            my_group.identifier
        )
        assert(my_user in my_group.users)

    def test_can_add_non_existent_user_to_non_existent_group(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        script_attributes_context = ScriptAttributesContext(
            task=None,
            environment_identifier="testing",
            process_instance_id=1,
            process_model_identifier="my_test_user",
        )
        result = AddUserToGroup().run(
            script_attributes_context,
            "dan@sartography.com",
            "competent-joes"
        )
        my_group = GroupModel.query.filter(GroupModel.identifier == "competent-joes").first()
        assert (my_group is not None)
        waiting_assignments = UserGroupAssignmentWaitingModel().query.filter_by(username="dan@sartography.com").first()
        assert (waiting_assignments is not None)
