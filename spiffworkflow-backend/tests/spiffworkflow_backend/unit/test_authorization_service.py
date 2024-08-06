import pytest
from flask import Flask
from flask.testing import FlaskClient
from spiffworkflow_backend.exceptions.error import InvalidPermissionError
from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.human_task_user import HumanTaskUserModel
from spiffworkflow_backend.models.user_group_assignment_waiting import UserGroupAssignmentWaitingModel
from spiffworkflow_backend.services.authorization_service import AuthorizationService
from spiffworkflow_backend.services.authorization_service import GroupPermissionsDict
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService
from spiffworkflow_backend.services.user_service import UserService

from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestAuthorizationService(BaseTest):
    def test_does_not_fail_if_user_not_created(self, app: Flask, with_db_and_bpmn_file_cleanup: None) -> None:
        AuthorizationService.import_permissions_from_yaml_file()

    def test_can_import_permissions_from_yaml(self, app: Flask, with_db_and_bpmn_file_cleanup: None) -> None:
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
        testadmin1_group_identifiers = sorted([g.identifier for g in users["testadmin1"].groups])
        assert testadmin1_group_identifiers == ["admin", "everybody"]
        assert len(users["testuser1"].groups) == 2
        testuser1_group_identifiers = sorted([g.identifier for g in users["testuser1"].groups])
        assert testuser1_group_identifiers == ["Finance Team", "everybody"]
        assert len(users["testuser2"].groups) == 3

        self.assert_user_has_permission(users["testuser1"], "update", "/v1.0/process-groups/finance:model1")
        self.assert_user_has_permission(users["testuser1"], "update", "/v1.0/process-groups/finance")
        self.assert_user_has_permission(users["testuser1"], "update", "/v1.0/process-groups/", expected_result=False)
        self.assert_user_has_permission(users["testuser4"], "read", "/v1.0/process-groups/finance:model1")
        self.assert_user_has_permission(users["testuser2"], "update", "/v1.0/process-groups/finance:model1")
        self.assert_user_has_permission(users["testuser2"], "update", "/v1.0/process-groups", expected_result=False)
        self.assert_user_has_permission(users["testuser2"], "read", "/v1.0/process-groups")
        self.assert_user_has_permission(users["testuser2"], "update", "/v1.0/process-groups", expected_result=False)

    def test_user_can_be_added_to_human_task_on_first_login(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        initiator_user = self.find_or_create_user("initiator_user")
        assert initiator_user.principal is not None
        # to ensure there is a user that can be assigned to the task
        self.find_or_create_user("testuser1")
        AuthorizationService.import_permissions_from_yaml_file()

        process_model = load_test_spec(
            process_model_id="test_group/model_with_lanes",
            bpmn_file_name="lanes.bpmn",
            process_model_source_directory="model_with_lanes",
        )

        process_instance = self.create_process_instance_from_process_model(process_model=process_model, user=initiator_user)
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)
        human_task = process_instance.active_human_tasks[0]
        spiff_task = processor.__class__.get_task_by_bpmn_identifier(human_task.task_name, processor.bpmn_process_instance)
        ProcessInstanceService.complete_form_task(processor, spiff_task, {}, initiator_user, human_task)

        human_task = process_instance.active_human_tasks[0]
        spiff_task = processor.__class__.get_task_by_bpmn_identifier(human_task.task_name, processor.bpmn_process_instance)
        finance_user = AuthorizationService.create_user_from_sign_in(
            {
                "username": "testuser2",
                "sub": "testuser2",
                "iss": "https://test.stuff",
                "email": "testuser2",
            }
        )
        ProcessInstanceService.complete_form_task(processor, spiff_task, {}, finance_user, human_task)

    def test_explode_permissions_all_on_process_group(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        expected_permissions = sorted(
            [
                ("/event-error-details/some-process-group:some-process-model:*", "read"),
                ("/logs/some-process-group:some-process-model:*", "read"),
                ("/logs/typeahead-filter-values/some-process-group:some-process-model:*", "read"),
                ("/message-models/some-process-group:some-process-model:*", "read"),
                ("/process-data/some-process-group:some-process-model:*", "read"),
                (
                    "/process-data-file-download/some-process-group:some-process-model:*",
                    "read",
                ),
                ("/process-groups/some-process-group:some-process-model:*", "create"),
                ("/process-groups/some-process-group:some-process-model:*", "delete"),
                ("/process-groups/some-process-group:some-process-model:*", "read"),
                ("/process-groups/some-process-group:some-process-model:*", "update"),
                (
                    "/process-instance-migrate/some-process-group:some-process-model:*",
                    "create",
                ),
                (
                    "/process-instance-suspend/some-process-group:some-process-model:*",
                    "create",
                ),
                (
                    "/process-instance-terminate/some-process-group:some-process-model:*",
                    "create",
                ),
                (
                    "/process-instances/some-process-group:some-process-model:*",
                    "create",
                ),
                (
                    "/process-instances/some-process-group:some-process-model:*",
                    "delete",
                ),
                ("/process-instance-events/some-process-group:some-process-model:*", "read"),
                ("/process-instances/for-me/some-process-group:some-process-model:*", "read"),
                ("/process-instances/some-process-group:some-process-model:*", "read"),
                ("/process-model-natural-language/some-process-group:some-process-model:*", "create"),
                ("/process-model-publish/some-process-group:some-process-model:*", "create"),
                ("/process-model-tests/create/some-process-group:some-process-model:*", "create"),
                ("/process-model-tests/run/some-process-group:some-process-model:*", "create"),
                ("/process-models/some-process-group:some-process-model:*", "create"),
                ("/process-models/some-process-group:some-process-model:*", "delete"),
                ("/process-models/some-process-group:some-process-model:*", "read"),
                ("/process-models/some-process-group:some-process-model:*", "update"),
                ("/task-assign/some-process-group:some-process-model:*", "create"),
                ("/task-data/some-process-group:some-process-model:*", "read"),
                ("/task-data/some-process-group:some-process-model:*", "update"),
            ]
        )
        permissions_to_assign = AuthorizationService.explode_permissions("all", "PG:/some-process-group/some-process-model")
        permissions_to_assign_tuples = sorted([(p.target_uri, p.permission) for p in permissions_to_assign])
        assert permissions_to_assign_tuples == expected_permissions

    def test_explode_permissions_start_on_process_group(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        expected_permissions = sorted(
            [
                ("/event-error-details/some-process-group:some-process-model:*", "read"),
                (
                    "/logs/some-process-group:some-process-model:*",
                    "read",
                ),
                (
                    "/logs/typeahead-filter-values/some-process-group:some-process-model:*",
                    "read",
                ),
                (
                    "/process-data-file-download/some-process-group:some-process-model:*",
                    "read",
                ),
                ("/process-instance-events/some-process-group:some-process-model:*", "read"),
                (
                    "/process-instances/for-me/some-process-group:some-process-model:*",
                    "read",
                ),
                ("/process-instances/some-process-group:some-process-model:*", "create"),
            ]
        )
        permissions_to_assign = AuthorizationService.explode_permissions("start", "PG:/some-process-group/some-process-model")
        permissions_to_assign_tuples = sorted([(p.target_uri, p.permission) for p in permissions_to_assign])
        assert permissions_to_assign_tuples == expected_permissions

    def test_explode_permissions_all_on_process_model(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        expected_permissions = sorted(
            [
                ("/event-error-details/some-process-group:some-process-model/*", "read"),
                ("/logs/some-process-group:some-process-model/*", "read"),
                (
                    "/process-data-file-download/some-process-group:some-process-model/*",
                    "read",
                ),
                ("/logs/typeahead-filter-values/some-process-group:some-process-model/*", "read"),
                ("/message-models/some-process-group:some-process-model/*", "read"),
                ("/process-data/some-process-group:some-process-model/*", "read"),
                (
                    "/process-instance-migrate/some-process-group:some-process-model/*",
                    "create",
                ),
                (
                    "/process-instance-suspend/some-process-group:some-process-model/*",
                    "create",
                ),
                (
                    "/process-instance-terminate/some-process-group:some-process-model/*",
                    "create",
                ),
                (
                    "/process-instances/some-process-group:some-process-model/*",
                    "create",
                ),
                (
                    "/process-instances/some-process-group:some-process-model/*",
                    "delete",
                ),
                ("/process-instance-events/some-process-group:some-process-model/*", "read"),
                ("/process-instances/for-me/some-process-group:some-process-model/*", "read"),
                ("/process-instances/some-process-group:some-process-model/*", "read"),
                ("/process-model-natural-language/some-process-group:some-process-model/*", "create"),
                ("/process-model-publish/some-process-group:some-process-model/*", "create"),
                ("/process-model-tests/create/some-process-group:some-process-model/*", "create"),
                ("/process-model-tests/run/some-process-group:some-process-model/*", "create"),
                ("/process-models/some-process-group:some-process-model/*", "create"),
                ("/process-models/some-process-group:some-process-model/*", "delete"),
                ("/process-models/some-process-group:some-process-model/*", "read"),
                ("/process-models/some-process-group:some-process-model/*", "update"),
                ("/task-assign/some-process-group:some-process-model/*", "create"),
                ("/task-data/some-process-group:some-process-model/*", "read"),
                ("/task-data/some-process-group:some-process-model/*", "update"),
            ]
        )
        permissions_to_assign = AuthorizationService.explode_permissions("all", "PM:/some-process-group/some-process-model")
        permissions_to_assign_tuples = sorted([(p.target_uri, p.permission) for p in permissions_to_assign])
        assert permissions_to_assign_tuples == expected_permissions

    def test_explode_permissions_start_on_process_model(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        expected_permissions = sorted(
            [
                (
                    "/event-error-details/some-process-group:some-process-model/*",
                    "read",
                ),
                (
                    "/logs/some-process-group:some-process-model/*",
                    "read",
                ),
                ("/logs/typeahead-filter-values/some-process-group:some-process-model/*", "read"),
                (
                    "/process-data-file-download/some-process-group:some-process-model/*",
                    "read",
                ),
                ("/process-instance-events/some-process-group:some-process-model/*", "read"),
                (
                    "/process-instances/for-me/some-process-group:some-process-model/*",
                    "read",
                ),
                ("/process-instances/some-process-group:some-process-model/*", "create"),
            ]
        )
        permissions_to_assign = AuthorizationService.explode_permissions("start", "PM:/some-process-group/some-process-model")
        permissions_to_assign_tuples = sorted([(p.target_uri, p.permission) for p in permissions_to_assign])
        assert permissions_to_assign_tuples == expected_permissions

    def test_explode_permissions_basic(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        expected_permissions = self._expected_basic_permissions()
        permissions_to_assign = AuthorizationService.explode_permissions("all", "BASIC")
        permissions_to_assign_tuples = sorted([(p.target_uri, p.permission) for p in permissions_to_assign])
        assert permissions_to_assign_tuples == expected_permissions

    def test_explode_permissions_support(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        expected_permissions = self._expected_support_permissions()
        permissions_to_assign = AuthorizationService.explode_permissions("all", "SUPPORT")
        permissions_to_assign_tuples = sorted([(p.target_uri, p.permission) for p in permissions_to_assign])
        assert permissions_to_assign_tuples == expected_permissions

    def test_explode_permissions_elevated(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        expected_permissions = self._expected_elevated_permissions()
        permissions_to_assign = AuthorizationService.explode_permissions("all", "ELEVATED")
        permissions_to_assign_tuples = sorted([(p.target_uri, p.permission) for p in permissions_to_assign])
        assert permissions_to_assign_tuples == expected_permissions

    def test_explode_permissions_all(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        expected_permissions = [
            ("/*", "create"),
            ("/*", "delete"),
            ("/*", "read"),
            ("/*", "update"),
        ]
        permissions_to_assign = AuthorizationService.explode_permissions("all", "ALL")
        permissions_to_assign_tuples = sorted([(p.target_uri, p.permission) for p in permissions_to_assign])
        assert permissions_to_assign_tuples == expected_permissions

    def test_explode_permissions_with_target_uri(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        expected_permissions = [
            ("/hey/model", "create"),
            ("/hey/model", "delete"),
            ("/hey/model", "read"),
            ("/hey/model", "update"),
        ]
        permissions_to_assign = AuthorizationService.explode_permissions("all", "/hey/model")
        permissions_to_assign_tuples = sorted([(p.target_uri, p.permission) for p in permissions_to_assign])
        assert permissions_to_assign_tuples == expected_permissions

    def test_granting_access_to_group_gives_access_to_group_and_subgroups(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        user = self.find_or_create_user(username="user_one")
        user_group = UserService.find_or_create_group("group_one")
        UserService.add_user_to_group(user, user_group)
        AuthorizationService.add_permission_from_uri_or_macro(user_group.identifier, "read", "PG:hey")
        self.assert_user_has_permission(user, "read", "/v1.0/process-groups/hey")
        self.assert_user_has_permission(user, "read", "/v1.0/process-groups/hey:yo")

    # https://github.com/sartography/spiff-arena/issues/1090 describes why we need access to process_group_show for parents
    def test_granting_access_to_subgroup_gives_access_to_subgroup_its_subgroups_and_even_show_for_its_parents(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        user = self.find_or_create_user(username="user_one")
        user_group = UserService.find_or_create_group("group_one")
        UserService.add_user_to_group(user, user_group)
        AuthorizationService.add_permission_from_uri_or_macro(user_group.identifier, "read", "PG:anotherprefix:yo")
        assert AuthorizationService.is_user_allowed_to_view_process_group_with_id(user, "hey") is False

        AuthorizationService.add_permission_from_uri_or_macro(user_group.identifier, "read", "PG:/hey/yo")
        AuthorizationService.add_permission_from_uri_or_macro(user_group.identifier, "DENY:read", "PG:hey:yo:who")
        assert AuthorizationService.is_user_allowed_to_view_process_group_with_id(user, "hey")
        assert AuthorizationService.is_user_allowed_to_view_process_group_with_id(user, "hey/yo")
        assert AuthorizationService.is_user_allowed_to_view_process_group_with_id(user, "hey:yo")
        assert AuthorizationService.is_user_allowed_to_view_process_group_with_id(user, "hey/yo/who") is False
        assert AuthorizationService.is_user_allowed_to_view_process_group_with_id(user, "hey/yo/who/what") is False

    def test_granting_access_to_model_gives_access_to_process_group_show_for_parent_groups_to_allow_navigating_to_model(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        user = self.find_or_create_user(username="user_one")
        user_group = UserService.find_or_create_group("group_one")
        UserService.add_user_to_group(user, user_group)
        AuthorizationService.add_permission_from_uri_or_macro(user_group.identifier, "read", "PM:hey:yo:wow:hot")
        assert AuthorizationService.is_user_allowed_to_view_process_group_with_id(user, "hey")
        assert AuthorizationService.is_user_allowed_to_view_process_group_with_id(user, "hey/yo")
        assert AuthorizationService.is_user_allowed_to_view_process_group_with_id(user, "hey/yo/wow")

    def test_explode_permissions_with_invalid_target_uri(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        with pytest.raises(InvalidPermissionError):
            AuthorizationService.explode_permissions("all", "BAD_MACRO")

    def test_explode_permissions_with_start_to_incorrect_target(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        with pytest.raises(InvalidPermissionError):
            AuthorizationService.explode_permissions("start", "/hey/model")

    def test_can_refresh_permissions(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        user = self.find_or_create_user(username="user_one")
        user_two = self.find_or_create_user(username="user_two")
        admin_user = self.find_or_create_user(username="testadmin1")

        # this group is not mentioned so it will get deleted
        UserService.find_or_create_group("group_two")
        assert GroupModel.query.filter_by(identifier="group_two").first() is not None

        UserService.find_or_create_group("group_three")
        assert GroupModel.query.filter_by(identifier="group_three").first() is not None

        group_info: list[GroupPermissionsDict] = [
            {
                "users": ["user_one", "user_two"],
                "name": "group_one",
                "permissions": [{"actions": ["create", "read"], "uri": "PG:hey"}],
            },
            {
                "users": ["user_two"],
                "name": "group_three",
                "permissions": [{"actions": ["create", "read"], "uri": "PG:hey2"}],
            },
            {
                "users": [],
                "name": "everybody",
                "permissions": [{"actions": ["read"], "uri": "PG:hey2everybody"}],
            },
        ]
        AuthorizationService.refresh_permissions(group_info)
        assert GroupModel.query.filter_by(identifier="group_two").first() is None
        assert GroupModel.query.filter_by(identifier="group_one").first() is not None
        self.assert_user_has_permission(admin_user, "create", "/v1.0/process-groups/whatever")
        self.assert_user_has_permission(user, "read", "/v1.0/process-groups/hey")
        self.assert_user_has_permission(user, "read", "/v1.0/process-groups/hey:yo")
        self.assert_user_has_permission(user, "create", "/v1.0/process-groups/hey:yo")
        self.assert_user_has_permission(user, "read", "/v1.0/process-groups/hey2everybody:yo")

        self.assert_user_has_permission(user_two, "read", "/v1.0/process-groups/hey")
        self.assert_user_has_permission(user_two, "read", "/v1.0/process-groups/hey:yo")
        self.assert_user_has_permission(user_two, "create", "/v1.0/process-groups/hey:yo")
        assert GroupModel.query.filter_by(identifier="group_three").first() is not None
        self.assert_user_has_permission(user_two, "read", "/v1.0/process-groups/hey2")
        self.assert_user_has_permission(user_two, "read", "/v1.0/process-groups/hey2:yo")
        self.assert_user_has_permission(user_two, "create", "/v1.0/process-groups/hey2:yo")

        # remove access to 'hey' from user_two
        group_info = [
            {
                "users": ["user_one"],
                "name": "group_one",
                "permissions": [{"actions": ["read"], "uri": "PG:hey"}],
            },
            {
                "users": ["user_two"],
                "name": "group_three",
                "permissions": [{"actions": ["create", "read"], "uri": "PG:hey2"}],
            },
        ]
        AuthorizationService.refresh_permissions(group_info)
        assert GroupModel.query.filter_by(identifier="group_one").first() is not None
        self.assert_user_has_permission(user, "read", "/v1.0/process-groups/hey")
        self.assert_user_has_permission(user, "read", "/v1.0/process-groups/hey:yo")
        self.assert_user_has_permission(user, "create", "/v1.0/process-groups/hey:yo", expected_result=False)
        self.assert_user_has_permission(admin_user, "create", "/v1.0/process-groups/whatever")

        self.assert_user_has_permission(user_two, "read", "/v1.0/process-groups/hey", expected_result=False)
        assert GroupModel.query.filter_by(identifier="group_three").first() is not None
        self.assert_user_has_permission(user_two, "read", "/v1.0/process-groups/hey2")
        self.assert_user_has_permission(user_two, "read", "/v1.0/process-groups/hey2:yo")
        self.assert_user_has_permission(user_two, "create", "/v1.0/process-groups/hey2:yo")

    def test_target_uri_matches_actual_uri(self, app: Flask, with_db_and_bpmn_file_cleanup: None) -> None:
        # exact match
        assert AuthorizationService.target_uri_matches_actual_uri("/process-groups/hey", "/process-groups/hey")
        # wildcard
        assert AuthorizationService.target_uri_matches_actual_uri("/process-groups/%", "/process-groups/hey")
        # wildcard is magical
        assert AuthorizationService.target_uri_matches_actual_uri("/process-groups/%", "/process-groups")
        # no match, since prefix doesn't match. wildcard isn't that magical.
        assert AuthorizationService.target_uri_matches_actual_uri("/process-groups/%", "/process-models") is False

    def _expected_basic_permissions(self) -> list[tuple[str, str]]:
        return sorted(
            [
                ("/active-users/*", "create"),
                ("/connector-proxy/typeahead/*", "read"),
                ("/debug/version-info", "read"),
                ("/extensions", "read"),
                ("/onboarding", "read"),
                ("/process-groups", "read"),
                ("/process-instances/find-by-id/*", "read"),
                ("/process-instances/for-me", "create"),
                ("/process-instances/for-me/*", "read"),
                ("/process-instances/report-metadata", "read"),
                ("/process-instances/reports/*", "create"),
                ("/process-instances/reports/*", "delete"),
                ("/process-instances/reports/*", "read"),
                ("/process-instances/reports/*", "update"),
                ("/process-models", "read"),
                ("/processes", "read"),
                ("/processes/callers/*", "read"),
                ("/public/*", "create"),
                ("/public/*", "delete"),
                ("/public/*", "read"),
                ("/public/*", "update"),
                ("/script-assist/enabled", "read"),
                ("/script-assist/process-message", "create"),
                ("/service-tasks", "read"),
                ("/tasks/*", "create"),
                ("/tasks/*", "delete"),
                ("/tasks/*", "read"),
                ("/tasks/*", "update"),
                ("/user-groups/for-current-user", "read"),
                ("/users/exists/by-username", "create"),
                ("/users/search", "read"),
                ("/upsearch-locations", "read"),
            ]
        )

    def _expected_support_permissions(self) -> list[tuple[str, str]]:
        return sorted(
            self._expected_basic_permissions()
            + [
                ("/can-run-privileged-script/*", "create"),
                ("/data-stores/*", "read"),
                ("/debug/*", "create"),
                ("/event-error-details/*", "read"),
                ("/extensions-get-data/*", "read"),
                ("/extensions/*", "create"),
                ("/logs/*", "read"),
                ("/messages", "read"),
                ("/messages/*", "create"),
                ("/process-data-file-download/*", "read"),
                ("/process-data/*", "read"),
                ("/process-instance-events/*", "read"),
                ("/process-instance-migrate/*", "create"),
                ("/process-instance-reset/*", "create"),
                ("/process-instance-resume/*", "create"),
                ("/process-instance-suspend/*", "create"),
                ("/process-instance-terminate/*", "create"),
                ("/process-instances/*", "create"),
                ("/process-instances/*", "delete"),
                ("/process-instances/*", "read"),
                ("/process-instances/*", "update"),
                ("/send-event/*", "create"),
                ("/task-assign/*", "create"),
                ("/task-complete/*", "create"),
                ("/task-data/*", "update"),
                ("/task-data/*", "read"),
            ]
        )

    def _expected_elevated_permissions(self) -> list[tuple[str, str]]:
        return sorted(
            self._expected_support_permissions()
            + [
                ("/authentication/configuration", "read"),
                ("/authentication/configuration", "update"),
                ("/authentication_begin/*", "read"),
                ("/authentications", "read"),
                ("/secrets/*", "create"),
                ("/secrets/*", "delete"),
                ("/secrets/*", "read"),
                ("/secrets/*", "update"),
                ("/service-accounts", "create"),
            ]
        )

    def test_can_refresh_permissions_with_regexes(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        user_regex = "REGEX:^user_.*"
        user = self.find_or_create_user(username="user_one")
        user_two = self.find_or_create_user(username="second_user_to_not_match_regex")

        # this group is not mentioned so it will get deleted
        UserService.find_or_create_group("group_two")
        assert GroupModel.query.filter_by(identifier="group_two").first() is not None

        UserService.find_or_create_group("group_three")
        assert GroupModel.query.filter_by(identifier="group_three").first() is not None

        group_info: list[GroupPermissionsDict] = [
            {
                "users": [user_regex],
                "name": "group_one",
                "permissions": [{"actions": ["create", "read"], "uri": "PG:hey"}],
            }
        ]
        AuthorizationService.refresh_permissions(group_info)
        waiting_assignments = UserGroupAssignmentWaitingModel.query.filter_by(username=user_regex).all()
        assert len(waiting_assignments) == 1
        assert waiting_assignments[0].username == user_regex
        assert len(user.groups) == 2
        assert "group_one" in [g.identifier for g in user.groups]
        self.assert_user_has_permission(user, "read", "/v1.0/process-groups/hey")
        self.assert_user_has_permission(user_two, "read", "/v1.0/process-groups/hey", expected_result=False)

        # run again to ensure the user does NOT lose permission when refreshing permissions again
        AuthorizationService.refresh_permissions(group_info)
        waiting_assignments = UserGroupAssignmentWaitingModel.query.filter_by(username=user_regex).all()
        assert len(waiting_assignments) == 1
        assert waiting_assignments[0].username == user_regex
        assert len(user.groups) == 2
        assert "group_one" in [g.identifier for g in user.groups]
        self.assert_user_has_permission(user, "read", "/v1.0/process-groups/hey")

        user_three_dict = {
            "username": "user_three",
            "email": "user_three@example.com",
            "iss": "test_service",
            "sub": "unique_id_three",
        }
        # create the user using the same method that login uses by default as a sanity check
        # and since we are testing the authorization service here anyway
        user_three = AuthorizationService.create_user_from_sign_in(user_three_dict)
        assert user_three is not None
        group_identifiers = sorted([g.identifier for g in user_three.groups])
        assert group_identifiers == ["everybody", "group_one"]
        self.assert_user_has_permission(user_three, "read", "/v1.0/process-groups/hey")

        # removing the regex removes permissions as well
        group_info = [
            {
                "users": ["second_user_to_not_match_regex"],
                "name": "group_one",
                "permissions": [{"actions": ["create", "read"], "uri": "PG:hey"}],
            }
        ]
        AuthorizationService.refresh_permissions(group_info)
        waiting_assignments = UserGroupAssignmentWaitingModel.query.filter_by(username=user_regex).all()
        assert len(waiting_assignments) == 0
        self.assert_user_has_permission(user, "read", "/v1.0/process-groups/hey", expected_result=False)
        self.assert_user_has_permission(user_three, "read", "/v1.0/process-groups/hey", expected_result=False)
        self.assert_user_has_permission(user_two, "read", "/v1.0/process-groups/hey", expected_result=True)

        waiting_assignments = UserGroupAssignmentWaitingModel.query.all()
        # ensure we didn't delete all of the user group assignments
        assert len(waiting_assignments) > 0

    def test_can_deny_access_with_permission(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        user = self.find_or_create_user(username="user_one")
        user_group = UserService.find_or_create_group("group_one")
        UserService.add_user_to_group(user, user_group)
        AuthorizationService.add_permission_from_uri_or_macro(user_group.identifier, "read", "PG:hey")
        AuthorizationService.add_permission_from_uri_or_macro(user_group.identifier, "DENY:read", "PG:hey:yo")
        AuthorizationService.add_permission_from_uri_or_macro(user_group.identifier, "DENY:read", "/process-groups/hey:new")

        self.assert_user_has_permission(user, "read", "/v1.0/process-groups/hey")

        # test specific uri deny
        self.assert_user_has_permission(user, "read", "/v1.0/process-groups/hey:yo", expected_result=False)
        self.assert_user_has_permission(user, "read", "/v1.0/process-groups/hey:yo:me", expected_result=False)

        # test wildcard deny
        self.assert_user_has_permission(user, "read", "/v1.0/process-groups/hey:new", expected_result=False)
        self.assert_user_has_permission(user, "read", "/v1.0/process-groups/hey:new:group", expected_result=True)

        # test it can be permitted again
        AuthorizationService.add_permission_from_uri_or_macro(user_group.identifier, "read", "PG:hey:yo")
        self.assert_user_has_permission(user, "read", "/v1.0/process-groups/hey:yo", expected_result=True)

    def test_adds_and_removes_user_from_human_task_assignments_when_group_updates(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_model = load_test_spec(
            process_model_id="test_group/model_with_lanes",
            process_model_source_directory="model_with_lanes",
            bpmn_file_name="lanes.bpmn",
        )
        process_instance = self.create_process_instance_from_process_model(process_model)
        user_one = self.find_or_create_user(username="user_one")
        user_group = UserService.find_or_create_group("Finance Team")
        UserService.add_user_to_group(user_one, user_group)
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)
        self.complete_next_manual_task(processor)

        with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_OPEN_ID_IS_AUTHORITY_FOR_USER_GROUPS", True):
            user_two = AuthorizationService.create_user_from_sign_in(
                {
                    "username": "user_two",
                    "sub": "user_two",
                    "iss": "https://test.stuff",
                    "email": "user_two@example.com",
                    "groups": ["Finance Team", "tmp_group"],
                }
            )
            assert len(user_two.groups) == 3
            # sometimes F comes be e
            assert sorted([g.identifier for g in user_two.groups]) == sorted(["Finance Team", "everybody", "tmp_group"])
            tmp_group = GroupModel.query.filter_by(identifier="tmp_group").first()
            assert tmp_group is not None
            assert tmp_group.source_is_open_id is True

            human_task_users = HumanTaskUserModel.query.filter_by(user_id=user_two.id).all()
            assert len(human_task_users) == 1

            user_two = AuthorizationService.create_user_from_sign_in(
                {
                    "username": "user_two",
                    "sub": "user_two",
                    "iss": "https://test.stuff",
                    "email": "user_two@example.com",
                    "groups": [],
                }
            )
            assert len(user_two.groups) == 1
            assert user_two.groups[0].identifier == "everybody"
            human_task_users = HumanTaskUserModel.query.filter_by(user_id=user_two.id).all()
            assert len(human_task_users) == 0
            tmp_group = GroupModel.query.filter_by(identifier="tmp_group").first()
            assert tmp_group is not None

            ##### run test again but this time without the groups key at all to remove groups
            user_two = AuthorizationService.create_user_from_sign_in(
                {
                    "username": "user_two",
                    "sub": "user_two",
                    "iss": "https://test.stuff",
                    "email": "user_two@example.com",
                    "groups": ["Finance Team", "tmp_group"],
                }
            )
            assert len(user_two.groups) == 3
            assert sorted([g.identifier for g in user_two.groups]) == sorted(["Finance Team", "everybody", "tmp_group"])
            tmp_group = GroupModel.query.filter_by(identifier="tmp_group").first()
            assert tmp_group is not None
            assert tmp_group.source_is_open_id is True
            human_task_users = HumanTaskUserModel.query.filter_by(user_id=user_two.id).all()
            assert len(human_task_users) == 1
            user_two = AuthorizationService.create_user_from_sign_in(
                {
                    "username": "user_two",
                    "sub": "user_two",
                    "iss": "https://test.stuff",
                    "email": "user_two@example.com",
                }
            )
            assert len(user_two.groups) == 1
            assert user_two.groups[0].identifier == "everybody"
            human_task_users = HumanTaskUserModel.query.filter_by(user_id=user_two.id).all()
            assert len(human_task_users) == 0
            tmp_group = GroupModel.query.filter_by(identifier="tmp_group").first()
            assert tmp_group is not None

    def test_user_can_complete_all_tasks_after_assignment(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_model = load_test_spec(
            process_model_id="test_group/model_with_lanes",
            process_model_source_directory="model_with_lanes",
            bpmn_file_name="lanes_with_extra_tasks.bpmn",
        )
        process_instance = self.create_process_instance_from_process_model(process_model)
        user_one = self.find_or_create_user(username="user_one")
        user_group = UserService.find_or_create_group("Finance Team")
        UserService.add_user_to_group(user_one, user_group)
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)
        self.complete_next_manual_task(processor, data={"itemId": "item1", "itemName": "Item One"})

        with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_OPEN_ID_IS_AUTHORITY_FOR_USER_GROUPS", True):
            user_two = AuthorizationService.create_user_from_sign_in(
                {
                    "username": "user_two",
                    "sub": "user_two",
                    "iss": "https://test.stuff",
                    "email": "user_two@example.com",
                    "groups": ["Finance Team"],
                }
            )
            human_task_users = (
                HumanTaskUserModel.query.filter_by(user_id=user_two.id)
                .join(HumanTaskModel)
                .filter(HumanTaskModel.completed == False)  # noqa: E712
                .all()
            )
            assert len(human_task_users) == 1
            self.complete_next_manual_task(processor, user=user_two)
            human_task_users = (
                HumanTaskUserModel.query.filter_by(user_id=user_two.id)
                .join(HumanTaskModel)
                .filter(HumanTaskModel.completed == False)  # noqa: E712
                .all()
            )
            assert len(human_task_users) == 1
            self.complete_next_manual_task(processor, user=user_two)

            user_two = AuthorizationService.create_user_from_sign_in(
                {
                    "username": "user_two",
                    "sub": "user_two",
                    "iss": "https://test.stuff",
                    "email": "user_two@example.com",
                }
            )
            human_task_count = (
                HumanTaskUserModel.query.join(HumanTaskModel)
                .filter(HumanTaskUserModel.user_id == user_two.id, HumanTaskModel.completed == True)  # noqa: E712
                .count()
            )
            assert human_task_count == 2

    def test_user_can_is_not_assigned_task_if_lane_owners_in_use(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_model = load_test_spec(
            process_model_id="test_group/model_with_lanes",
            process_model_source_directory="model_with_lanes",
            bpmn_file_name="lanes_with_lane_owners.bpmn",
        )
        process_instance = self.create_process_instance_from_process_model(process_model)
        user_one = self.find_or_create_user(username="user_one")
        user_group = UserService.find_or_create_group("/Infra")
        UserService.add_user_to_group(user_one, user_group)
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)
        self.complete_next_manual_task(processor, data={"itemId": "item1", "itemName": "Item One"})

        with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_OPEN_ID_IS_AUTHORITY_FOR_USER_GROUPS", True):
            user_two = AuthorizationService.create_user_from_sign_in(
                {
                    "username": "user_two",
                    "sub": "user_two",
                    "iss": "https://test.stuff",
                    "email": "user_two@example.com",
                    "groups": ["/Infra"],
                }
            )
            human_task_users = HumanTaskUserModel.query.filter_by(user_id=user_two.id).all()
            assert len(human_task_users) == 0
