"""Test_get_localtime."""
from flask.app import Flask
from flask_bpmn.models.db import db
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec

from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.services.process_instance_processor import (
    ProcessInstanceProcessor,
)
from spiffworkflow_backend.services.user_service import UserService


class TestGetGroupMembers(BaseTest):
    """TestGetGroupMembers."""

    def test_can_get_members_of_a_group(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        """Test_can_get_members_of_a_group."""
        initiator_user = self.find_or_create_user("initiator_user")
        testuser1 = self.find_or_create_user("testuser1")
        testuser2 = self.find_or_create_user("testuser2")
        testuser3 = self.find_or_create_user("testuser3")
        group_a = GroupModel(identifier="groupA")
        group_b = GroupModel(identifier="groupB")
        db.session.add(group_a)
        db.session.add(group_b)
        db.session.commit()

        UserService.add_user_to_group(testuser1, group_a)
        UserService.add_user_to_group(testuser2, group_a)
        UserService.add_user_to_group(testuser3, group_b)

        process_model = load_test_spec(
            process_model_id="get_group_members",
            bpmn_file_name="get_group_members.bpmn",
        )
        process_instance = self.create_process_instance_from_process_model(
            process_model=process_model, user=initiator_user
        )
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)

        assert processor.bpmn_process_instance.data
        assert processor.bpmn_process_instance.data["members_a"] == [
            "testuser1",
            "testuser2",
        ]
        assert processor.bpmn_process_instance.data["members_b"] == ["testuser3"]
