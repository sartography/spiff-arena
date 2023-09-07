import pytest
from flask import Flask
from flask.testing import FlaskClient
from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.services.authorization_service import AuthorizationService
from spiffworkflow_backend.services.authorization_service import GroupPermissionsDict
from spiffworkflow_backend.services.authorization_service import InvalidPermissionError
from spiffworkflow_backend.services.group_service import GroupService
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

        process_instance = self.create_process_instance_from_process_model(
            process_model=process_model, user=initiator_user
        )
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)
        human_task = process_instance.active_human_tasks[0]
        spiff_task = processor.__class__.get_task_by_bpmn_identifier(
            human_task.task_name, processor.bpmn_process_instance
        )
        ProcessInstanceService.complete_form_task(processor, spiff_task, {}, initiator_user, human_task)

        human_task = process_instance.active_human_tasks[0]
        spiff_task = processor.__class__.get_task_by_bpmn_identifier(
            human_task.task_name, processor.bpmn_process_instance
        )
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
                ("/process-instances/for-me/some-process-group:some-process-model:*", "read"),
                ("/process-instances/some-process-group:some-process-model:*", "read"),
                ("/process-model-natural-language/some-process-group:some-process-model:*", "create"),
                ("/process-model-publish/some-process-group:some-process-model:*", "create"),
                ("/process-model-tests/some-process-group:some-process-model:*", "create"),
                ("/process-models/some-process-group:some-process-model:*", "create"),
                ("/process-models/some-process-group:some-process-model:*", "delete"),
                ("/process-models/some-process-group:some-process-model:*", "read"),
                ("/process-models/some-process-group:some-process-model:*", "update"),
                ("/task-assign/some-process-group:some-process-model:*", "create"),
                ("/task-data/some-process-group:some-process-model:*", "read"),
                ("/task-data/some-process-group:some-process-model:*", "update"),
            ]
        )
        permissions_to_assign = AuthorizationService.explode_permissions(
            "all", "PG:/some-process-group/some-process-model"
        )
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
                (
                    "/process-instances/for-me/some-process-group:some-process-model:*",
                    "read",
                ),
                ("/process-instances/some-process-group:some-process-model:*", "create"),
            ]
        )
        permissions_to_assign = AuthorizationService.explode_permissions(
            "start", "PG:/some-process-group/some-process-model"
        )
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
                ("/process-data/some-process-group:some-process-model/*", "read"),
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
                ("/process-instances/for-me/some-process-group:some-process-model/*", "read"),
                ("/process-instances/some-process-group:some-process-model/*", "read"),
                ("/process-model-natural-language/some-process-group:some-process-model/*", "create"),
                ("/process-model-publish/some-process-group:some-process-model/*", "create"),
                ("/process-model-tests/some-process-group:some-process-model/*", "create"),
                ("/process-models/some-process-group:some-process-model/*", "create"),
                ("/process-models/some-process-group:some-process-model/*", "delete"),
                ("/process-models/some-process-group:some-process-model/*", "read"),
                ("/process-models/some-process-group:some-process-model/*", "update"),
                ("/task-assign/some-process-group:some-process-model/*", "create"),
                ("/task-data/some-process-group:some-process-model/*", "read"),
                ("/task-data/some-process-group:some-process-model/*", "update"),
            ]
        )
        permissions_to_assign = AuthorizationService.explode_permissions(
            "all", "PM:/some-process-group/some-process-model"
        )
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
                (
                    "/process-instances/for-me/some-process-group:some-process-model/*",
                    "read",
                ),
                ("/process-instances/some-process-group:some-process-model/*", "create"),
            ]
        )
        permissions_to_assign = AuthorizationService.explode_permissions(
            "start", "PM:/some-process-group/some-process-model"
        )
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
        user_group = GroupService.find_or_create_group("group_one")
        UserService.add_user_to_group(user, user_group)
        AuthorizationService.add_permission_from_uri_or_macro(user_group.identifier, "read", "PG:hey")
        self.assert_user_has_permission(user, "read", "/v1.0/process-groups/hey")
        self.assert_user_has_permission(user, "read", "/v1.0/process-groups/hey:yo")

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
        GroupService.find_or_create_group("group_two")
        assert GroupModel.query.filter_by(identifier="group_two").first() is not None

        GroupService.find_or_create_group("group_three")
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
                ("/process-instances/report-metadata", "read"),
                ("/process-instances/reports/*", "create"),
                ("/process-instances/reports/*", "delete"),
                ("/process-instances/reports/*", "read"),
                ("/process-instances/reports/*", "update"),
                ("/process-models", "read"),
                ("/processes", "read"),
                ("/processes/callers/*", "read"),
                ("/service-tasks", "read"),
                ("/tasks/*", "create"),
                ("/tasks/*", "delete"),
                ("/tasks/*", "read"),
                ("/tasks/*", "update"),
                ("/user-groups/for-current-user", "read"),
                ("/users/exists/by-username", "create"),
                ("/users/search", "read"),
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
            ]
        )
