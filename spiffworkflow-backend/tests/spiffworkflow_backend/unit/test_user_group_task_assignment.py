import time

from starlette.testclient import TestClient

from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.services.user_service import UserService
from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestUserGroupTaskAssignment(BaseTest):
    def test_newly_added_user_to_group_gets_access_to_existing_tasks(
        self,
        app,
        client: TestClient,
        with_db_and_bpmn_file_cleanup,
    ):
        # 1. Create a user 'nick'
        nick = self.find_or_create_user("nick")

        # 2. Create a group 'Awesome'
        awesome_group = UserService.find_or_create_group("Awesome")

        # 3. Create a process instance with a human task
        process_instance = ProcessInstanceModel(
            status="running",
            process_initiator=nick,
            process_model_identifier="test/process",
            process_model_display_name="Test Process",
            updated_at_in_seconds=round(time.time()),
            start_in_seconds=round(time.time()),
        )
        from spiffworkflow_backend.models.db import db

        db.session.add(process_instance)
        db.session.commit()

        human_task = HumanTaskModel(
            process_instance_id=process_instance.id,
            task_id="task_1",
            task_name="Task 1",
            task_type="UserTask",
            task_status="READY",
            lane_assignment_id=awesome_group.id,
            completed=False,
        )
        db.session.add(human_task)
        db.session.commit()

        # Verify nick is NOT a potential owner
        assert nick not in human_task.potential_owners

        # 4. Add 'nick' to 'Awesome'
        UserService.add_user_to_group(nick, awesome_group)

        # 5. Verify 'nick' is now a potential owner
        # We need to refresh the human_task object or its potential_owners relationship
        db.session.refresh(human_task)

        # This assertion should fail before the fix
        assert nick in human_task.potential_owners
