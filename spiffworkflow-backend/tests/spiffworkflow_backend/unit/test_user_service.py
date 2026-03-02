from flask.app import Flask
from starlette.testclient import TestClient

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.services.user_service import UserService
from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestUserService(BaseTest):
    def test_assigning_a_group_to_a_user_before_the_user_is_created(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        a_test_group = UserService.find_or_create_group("aTestGroup")
        UserService.add_waiting_group_assignment("initiator_user", a_test_group)
        initiator_user = self.find_or_create_user("initiator_user")
        assert initiator_user.groups[0] == a_test_group

    def test_assigning_a_group_to_all_users_updates_new_users(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        everybody_group = UserService.find_or_create_group("everybodyGroup")
        UserService.add_waiting_group_assignment("REGEX:.*", everybody_group)
        initiator_user = self.find_or_create_user("initiator_user")
        assert initiator_user.groups[0] == everybody_group

    def test_assigning_a_group_to_all_users_updates_existing_users(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        initiator_user = self.find_or_create_user("initiator_user")
        everybody_group = UserService.find_or_create_group("everybodyGroup")
        UserService.add_waiting_group_assignment("REGEX:.*", everybody_group)
        assert initiator_user.groups[0] == everybody_group

    def test_newly_added_user_to_group_gets_access_to_existing_tasks(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        user1 = self.find_or_create_user("user1")
        awesome_group = UserService.find_or_create_group("Awesome")
        process_instance = ProcessInstanceModel(
            process_initiator=user1,
            process_model_identifier="test/process",
            process_model_display_name="Test Process",
        )

        db.session.add(process_instance)
        db.session.commit()

        human_task = HumanTaskModel(
            process_instance_id=process_instance.id,
            task_id="task_1",
            task_name="Task 1",
            task_type="UserTask",
            task_status="READY",
            lane_assignment_id=awesome_group.id,
        )
        db.session.add(human_task)
        db.session.commit()

        assert user1 not in human_task.potential_owners
        UserService.add_user_to_group(user1, awesome_group)

        # We need to refresh the human_task object or its potential_owners relationship
        db.session.refresh(human_task)

        assert user1 in human_task.potential_owners
