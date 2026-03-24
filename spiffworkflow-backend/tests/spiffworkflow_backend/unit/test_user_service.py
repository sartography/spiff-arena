from flask.app import Flask
from starlette.testclient import TestClient

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.human_task_group import HumanTaskGroupModel
from spiffworkflow_backend.models.human_task_user import HumanTaskUserAddedBy
from spiffworkflow_backend.models.human_task_user import HumanTaskUserModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.services.user_service import UserService
from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestUserService(BaseTest):
    def test_group_membership_change_does_not_remove_explicit_lane_owner_assignment(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        explicit_owner_user = self.find_or_create_user("explicit_owner_user")
        process_initiator = self.find_or_create_user("process_initiator")
        lane_group = UserService.find_or_create_group("lane_group")

        process_instance = ProcessInstanceModel(
            process_initiator=process_initiator,
            process_model_identifier="test/process",
            process_model_display_name="Test Process",
        )
        db.session.add(process_instance)
        db.session.flush()

        human_task = HumanTaskModel(
            process_instance_id=process_instance.id,
            task_id="task_1",
            task_name="Task 1",
            task_type="UserTask",
            task_status="READY",
            lane_assignment_id=lane_group.id,
        )
        db.session.add(human_task)
        db.session.flush()
        db.session.add(
            HumanTaskUserModel(
                user_id=explicit_owner_user.id,
                human_task_id=human_task.id,
                added_by=HumanTaskUserAddedBy.lane_owner.value,
            )
        )
        db.session.commit()

        UserService.add_user_to_group(explicit_owner_user, lane_group)
        UserService.remove_user_from_group(explicit_owner_user, lane_group.id)

        assignment = HumanTaskUserModel.query.filter_by(user_id=explicit_owner_user.id, human_task_id=human_task.id).first()
        assert assignment is not None
        assert assignment.added_by == HumanTaskUserAddedBy.lane_owner.value

    def test_group_membership_change_does_not_assign_explicit_lane_owner_group_task_via_lane_group(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        lane_group_user = self.find_or_create_user("lane_group_user")
        process_initiator = self.find_or_create_user("process_initiator")
        lane_group = UserService.find_or_create_group("lane_group")
        explicit_owner_group = UserService.find_or_create_group("explicit_owner_group")

        process_instance = ProcessInstanceModel(
            process_initiator=process_initiator,
            process_model_identifier="test/process",
            process_model_display_name="Test Process",
        )
        db.session.add(process_instance)
        db.session.flush()

        human_task = HumanTaskModel(
            process_instance_id=process_instance.id,
            task_id="task_1",
            task_name="Task 1",
            task_type="UserTask",
            task_status="READY",
            lane_assignment_id=lane_group.id,
        )
        db.session.add(human_task)
        db.session.flush()
        db.session.add(HumanTaskGroupModel(human_task_id=human_task.id, group_id=explicit_owner_group.id))
        db.session.commit()

        UserService.add_user_to_group(lane_group_user, lane_group)

        assignment = HumanTaskUserModel.query.filter_by(user_id=lane_group_user.id, human_task_id=human_task.id).first()
        assert assignment is None

    def test_group_membership_changes_update_lane_owner_group_assignments(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        user_one = self.find_or_create_user("user_one")
        user_two = self.find_or_create_user("user_two")
        lane_group = UserService.find_or_create_group("lane_group")
        reviewers_group = UserService.find_or_create_group("reviewers")
        UserService.add_user_to_group(user_two, reviewers_group)

        process_instance = ProcessInstanceModel(
            process_initiator=user_two,
            process_model_identifier="test/process",
            process_model_display_name="Test Process",
        )
        db.session.add(process_instance)
        db.session.flush()

        human_task = HumanTaskModel(
            process_instance_id=process_instance.id,
            task_id="task_1",
            task_name="Task 1",
            task_type="UserTask",
            task_status="READY",
            lane_assignment_id=lane_group.id,
        )
        db.session.add(human_task)
        db.session.flush()

        db.session.add(HumanTaskGroupModel(human_task_id=human_task.id, group_id=reviewers_group.id))
        db.session.add(
            HumanTaskUserModel(
                user_id=user_two.id,
                human_task_id=human_task.id,
                added_by=HumanTaskUserAddedBy.lane_assignment.value,
            )
        )
        db.session.commit()

        UserService.add_user_to_group(user_one, reviewers_group)

        user_one_assignment = HumanTaskUserModel.query.filter_by(user_id=user_one.id, human_task_id=human_task.id).first()
        assert user_one_assignment is not None

        UserService.remove_user_from_group(user_one, reviewers_group.id)
        user_one_assignment_after_removal = HumanTaskUserModel.query.filter_by(
            user_id=user_one.id, human_task_id=human_task.id
        ).first()
        assert user_one_assignment_after_removal is None

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
