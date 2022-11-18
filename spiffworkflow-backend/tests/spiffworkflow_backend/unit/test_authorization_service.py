"""Test_message_service."""
import pytest
from flask import Flask
from flask.testing import FlaskClient
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.models.user import UserNotFoundError
from spiffworkflow_backend.services.authorization_service import AuthorizationService
from spiffworkflow_backend.services.process_instance_processor import (
    ProcessInstanceProcessor,
)
from spiffworkflow_backend.services.process_instance_service import (
    ProcessInstanceService,
)
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestAuthorizationService(BaseTest):
    """TestAuthorizationService."""

    def test_can_raise_if_missing_user(
        self, app: Flask, with_db_and_bpmn_file_cleanup: None
    ) -> None:
        """Test_can_raise_if_missing_user."""
        with pytest.raises(UserNotFoundError):
            AuthorizationService.import_permissions_from_yaml_file(
                raise_if_missing_user=True
            )

    def test_does_not_fail_if_user_not_created(
        self, app: Flask, with_db_and_bpmn_file_cleanup: None
    ) -> None:
        """Test_does_not_fail_if_user_not_created."""
        AuthorizationService.import_permissions_from_yaml_file()

    def test_can_import_permissions_from_yaml(
        self, app: Flask, with_db_and_bpmn_file_cleanup: None
    ) -> None:
        """Test_can_import_permissions_from_yaml."""
        usernames = [
            "testadmin1",
            "testadmin2",
            "testuser1",
            "testuser2",
            "testuser3",
            "testuser4",
        ]
        users = {}
        for username in usernames:
            user = self.find_or_create_user(username=username)
            users[username] = user

        AuthorizationService.import_permissions_from_yaml_file()
        assert len(users["testadmin1"].groups) == 2
        testadmin1_group_identifiers = sorted(
            [g.identifier for g in users["testadmin1"].groups]
        )
        assert testadmin1_group_identifiers == ["admin", "everybody"]
        assert len(users["testuser1"].groups) == 2
        testuser1_group_identifiers = sorted(
            [g.identifier for g in users["testuser1"].groups]
        )
        assert testuser1_group_identifiers == ["Finance Team", "everybody"]
        assert len(users["testuser2"].groups) == 3

        self.assert_user_has_permission(
            users["testuser1"], "update", "/v1.0/process-groups/finance/model1"
        )
        self.assert_user_has_permission(
            users["testuser1"], "update", "/v1.0/process-groups/finance/"
        )
        self.assert_user_has_permission(
            users["testuser1"], "update", "/v1.0/process-groups/", expected_result=False
        )
        self.assert_user_has_permission(
            users["testuser4"], "update", "/v1.0/process-groups/finance/model1"
        )
        # via the user, not the group
        self.assert_user_has_permission(
            users["testuser4"], "read", "/v1.0/process-groups/finance/model1"
        )
        self.assert_user_has_permission(
            users["testuser2"], "update", "/v1.0/process-groups/finance/model1"
        )
        self.assert_user_has_permission(
            users["testuser2"], "update", "/v1.0/process-groups/", expected_result=False
        )
        self.assert_user_has_permission(
            users["testuser2"], "read", "/v1.0/process-groups/"
        )

    def test_user_can_be_added_to_active_task_on_first_login(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_user_can_be_added_to_active_task_on_first_login."""
        initiator_user = self.find_or_create_user("initiator_user")
        assert initiator_user.principal is not None
        # to ensure there is a user that can be assigned to the task
        self.find_or_create_user("testuser1")
        AuthorizationService.import_permissions_from_yaml_file()

        process_model_identifier = self.create_group_and_model_with_bpmn(
            client=client,
            user=with_super_admin_user,
            process_group_id="test_group",
            process_model_id="model_with_lanes",
            bpmn_file_name="lanes.bpmn",
            bpmn_file_location="model_with_lanes",
        )

        process_model = ProcessModelService().get_process_model(
            process_model_id=process_model_identifier
        )
        process_instance = self.create_process_instance_from_process_model(
            process_model=process_model, user=initiator_user
        )
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)
        active_task = process_instance.active_tasks[0]
        spiff_task = processor.__class__.get_task_by_bpmn_identifier(
            active_task.task_name, processor.bpmn_process_instance
        )
        ProcessInstanceService.complete_form_task(
            processor, spiff_task, {}, initiator_user, active_task
        )

        active_task = process_instance.active_tasks[0]
        spiff_task = processor.__class__.get_task_by_bpmn_identifier(
            active_task.task_name, processor.bpmn_process_instance
        )
        finance_user = AuthorizationService.create_user_from_sign_in(
            {"username": "testuser2", "sub": "open_id"}
        )
        ProcessInstanceService.complete_form_task(
            processor, spiff_task, {}, finance_user, active_task
        )
