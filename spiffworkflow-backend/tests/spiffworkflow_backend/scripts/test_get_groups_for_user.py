from flask import g
from flask.app import Flask
from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.get_groups_for_user import GetGroupsForUser
from spiffworkflow_backend.services.user_service import UserService

from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestGetGroupsForUser(BaseTest):
    def test_get_groups_for_user(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        testuser1 = self.find_or_create_user("testuser1")
        group1 = UserService.find_or_create_group("group1")
        group2 = UserService.find_or_create_group("group2")
        UserService.find_or_create_group("group3")
        UserService.add_user_to_group(testuser1, group1)
        UserService.add_user_to_group(testuser1, group2)

        g.user = testuser1
        script_attributes_context = ScriptAttributesContext(
            task=None,
            environment_identifier="testing",
            process_instance_id=None,
            process_model_identifier=None,
        )
        result = GetGroupsForUser().run(
            script_attributes_context,
        )
        assert len(result) == 2
        group_names = [g["identifier"] for g in result]
        assert group_names == ["group1", "group2"]
