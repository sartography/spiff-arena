import json

from flask import g
from flask.app import Flask
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.get_current_user import GetCurrentUser

from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestGetCurrentUser(BaseTest):
    def test_get_current_user(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        testuser1 = self.find_or_create_user("testuser1")
        testuser1.tenant_specific_field_1 = "456"
        testuser1.display_name = "Test User NUMBER ONE!"
        db.session.add(testuser1)
        db.session.commit()

        testuser1 = self.find_or_create_user("testuser1")
        g.user = testuser1
        process_model_identifier = "test_process_model"
        process_instance_id = 1
        script_attributes_context = ScriptAttributesContext(
            task=None,
            environment_identifier="testing",
            process_instance_id=process_instance_id,
            process_model_identifier=process_model_identifier,
        )
        result = GetCurrentUser().run(
            script_attributes_context,
        )
        assert result["username"] == "testuser1"
        assert result["tenant_specific_field_1"] == "456"
        assert result["display_name"] == "Test User NUMBER ONE!"
        json.dumps(result)
