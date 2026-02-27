import json

import pytest
from flask.app import Flask

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.human_task_user import HumanTaskUserModel
from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.get_users_assigned_to_task import GetUsersAssignedToTask
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestGetUsersAssignedToTask(BaseTest):
    def test_get_users_assigned_to_task(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        user1 = self.find_or_create_user("testuser1")
        user2 = self.find_or_create_user("testuser2")
        user3 = self.find_or_create_user("testuser3")
        db.session.add_all([user1, user2, user3])
        db.session.commit()

        process_model = load_test_spec(
            "test_group/hello_world",
            bpmn_file_name="hello_world.bpmn",
            process_model_source_directory="hello_world",
        )

        process_instance = self.create_process_instance_from_process_model(process_model=process_model, user=user1)
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)

        assert len(process_instance.active_human_tasks) == 1
        human_task = process_instance.active_human_tasks[0]

        # The initiator, user1, is by default assigned as a potential owner for the task
        assert len(human_task.potential_owners) == 1
        assert human_task.potential_owners[0] == user1

        # Assign two more potential owners for the same human task
        db.session.add_all(
            [
                HumanTaskUserModel(human_task_id=human_task.id, user_id=user2.id, added_by="manual"),
                HumanTaskUserModel(human_task_id=human_task.id, user_id=user3.id, added_by="manual"),
            ]
        )
        db.session.commit()

        # Refresh relationship so potential_owners reflects the new join rows
        db.session.refresh(human_task)

        task_guid = human_task.task_guid
        assert task_guid is not None

        script_attributes_context = ScriptAttributesContext(
            task=None,
            environment_identifier="testing",
            process_instance_id=process_instance.id,
            process_model_identifier=process_model.id,
        )

        result = GetUsersAssignedToTask().run(script_attributes_context, task_guid=task_guid)

        assert result == ["testuser1", "testuser2", "testuser3"]
        json.dumps(result)

    def test_get_users_assigned_to_task_raises_if_no_task_guid(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        script_attributes_context = ScriptAttributesContext(
            task=None,
            environment_identifier="testing",
            process_instance_id=1,
            process_model_identifier="test_process_model",
        )

        with pytest.raises(ValueError, match="Expected task_guid as first argument or keyword argument"):
            GetUsersAssignedToTask().run(script_attributes_context)
