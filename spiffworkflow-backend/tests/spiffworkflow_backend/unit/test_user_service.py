"""Process Model."""
from flask.app import Flask
from flask.testing import FlaskClient
from tests.spiffworkflow_backend.helpers.base_test import BaseTest

from spiffworkflow_backend.models.user_group_assignment_waiting import (
    UserGroupAssignmentWaitingModel,
)
from spiffworkflow_backend.services.group_service import GroupService
from spiffworkflow_backend.services.user_service import UserService


class TestUserService(BaseTest):
    """TestUserService."""

    def test_assigning_a_group_to_a_user_before_the_user_is_created(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        """Test_waiting_group_assignments."""
        a_test_group = GroupService.find_or_create_group("aTestGroup")
        UserService.add_waiting_group_assignment("initiator_user", a_test_group)
        initiator_user = self.find_or_create_user("initiator_user")
        assert initiator_user.groups[0] == a_test_group

    def test_assigning_a_group_to_all_users_updates_new_users(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        """Test_waiting_group_assignments."""
        everybody_group = GroupService.find_or_create_group("everybodyGroup")
        UserService.add_waiting_group_assignment(
            UserGroupAssignmentWaitingModel.MATCH_ALL_USERS, everybody_group
        )
        initiator_user = self.find_or_create_user("initiator_user")
        assert initiator_user.groups[0] == everybody_group

    def test_assigning_a_group_to_all_users_updates_existing_users(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        """Test_waiting_group_assignments."""
        initiator_user = self.find_or_create_user("initiator_user")
        everybody_group = GroupService.find_or_create_group("everybodyGroup")
        UserService.add_waiting_group_assignment(
            UserGroupAssignmentWaitingModel.MATCH_ALL_USERS, everybody_group
        )
        assert initiator_user.groups[0] == everybody_group
