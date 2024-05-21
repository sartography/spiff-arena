import re

from flask import Flask
from spiffworkflow_backend.services.authorization_service import AuthorizationService
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.user_service import UserService

from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestProcessModelService(BaseTest):
    def test_can_update_specified_attributes(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_model = load_test_spec(
            "test_group/hello_world",
            bpmn_file_name="hello_world.bpmn",
            process_model_source_directory="hello_world",
        )
        assert process_model.display_name == "test_group/hello_world"

        primary_process_id = process_model.primary_process_id
        assert primary_process_id == "Process_HelloWorld"

        ProcessModelService.update_process_model(process_model, {"display_name": "new_name"})

        assert process_model.display_name == "new_name"
        assert process_model.primary_process_id == primary_process_id

    def test_can_get_file_contents(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_model = load_test_spec(
            "test_group/hello_world",
            bpmn_file_name="hello_world.bpmn",
            process_model_source_directory="hello_world",
        )
        assert process_model.display_name == "test_group/hello_world"

        primary_process_id = process_model.primary_process_id
        assert primary_process_id == "Process_HelloWorld"

        process_models = ProcessModelService.get_process_models(recursive=True, include_files=True)
        assert len(process_models) == 1

        pm_string = app.json.dumps(process_models[0])
        pm_dict = app.json.loads(pm_string)
        assert len(pm_dict["files"]) == 1
        file = pm_dict["files"][0]
        assert re.search("hello", file["file_contents"]) is not None

    def test_can_get_sub_process_groups_when_no_permission_to_parent(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        user = self.find_or_create_user(username="user_one")
        user_group = UserService.find_or_create_group("group_one")
        noread = "DENY:read"
        UserService.add_user_to_group(user, user_group)
        AuthorizationService.add_permission_from_uri_or_macro(user_group.identifier, "read", "PG:a1:b2:c2")
        AuthorizationService.add_permission_from_uri_or_macro(user_group.identifier, "read", "PG:a1:b2:c3:d1")
        AuthorizationService.add_permission_from_uri_or_macro(user_group.identifier, noread, "PG:a1:b2:c4")
        AuthorizationService.add_permission_from_uri_or_macro(user_group.identifier, "read", "PG:a1:b2:c4:d1")

        self.create_process_group("a1")
        self.create_process_group("a1/b1")
        self.create_process_group("a1/b2")
        self.create_process_group("a1/b3")
        self.create_process_group("a1/b2/c1")
        self.create_process_group("a1/b2/c2")
        self.create_process_group("a1/b2/c3")
        self.create_process_group("a1/b2/c4")
        self.create_process_group("a1/b2/c3/d1")
        self.create_process_group("a1/b2/c4/d1")

        process_groups = ProcessModelService.get_process_groups_for_api(user=user)
        assert len(process_groups) == 1
        assert process_groups[0].id == "a1"

        process_groups = ProcessModelService.get_process_groups_for_api("a1", user=user)
        assert len(process_groups) == 1
        assert process_groups[0].id == "a1/b2"

        process_groups = ProcessModelService.get_process_groups_for_api("a1/b2", user=user)
        pg_identifiers = [pg.id for pg in process_groups]
        assert len(pg_identifiers) == 2
        assert pg_identifiers == ["a1/b2/c2", "a1/b2/c3"]

        process_groups = ProcessModelService.get_process_groups_for_api("a1/b2/c4", user=user)
        assert len(process_groups) == 0
        process_groups = ProcessModelService.get_process_groups_for_api("a1/b2/c4/d1", user=user)
        assert len(process_groups) == 0

    def test_can_get_sub_process_models_when_no_permission_to_parent(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        user = self.find_or_create_user(username="user_one")
        user_group = UserService.find_or_create_group("group_one")
        noread = "DENY:read"
        UserService.add_user_to_group(user, user_group)
        AuthorizationService.add_permission_from_uri_or_macro(user_group.identifier, "read", "PM:a1:b2:pm3")
        AuthorizationService.add_permission_from_uri_or_macro(user_group.identifier, noread, "PM:a1:b2:pm4")
        AuthorizationService.add_permission_from_uri_or_macro(user_group.identifier, "DENY:read", "PM:a1:b3:c2")

        self.create_process_group("a1")
        self.create_process_group("a1/b1")
        self.create_process_group("a1/b2")
        self.create_process_group("a1/b3")
        self.create_process_model("a1/b2/pm1")
        self.create_process_model("a1/b2/pm2")
        self.create_process_model("a1/b2/pm3")
        self.create_process_model("a1/b2/pm4")
        self.create_process_group("a1/b3/c2")
        self.create_process_group("a1/b3/c2/pm1")

        process_groups = ProcessModelService.get_process_groups_for_api(user=user)
        assert len(process_groups) == 1
        assert process_groups[0].id == "a1"

        process_groups = ProcessModelService.get_process_groups_for_api("a1", user=user)
        pg_identifiers = [pg.id for pg in process_groups]
        assert len(pg_identifiers) == 1
        assert process_groups[0].id == "a1/b2"

    def test_get_process_models_for_api(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        user = BaseTest.create_user_with_permission("super_admin")
        process_model = load_test_spec(
            "test_group/hello_world",
            bpmn_file_name="hello_world.bpmn",
            process_model_source_directory="hello_world",
        )
        assert process_model.display_name == "test_group/hello_world"

        primary_process_id = process_model.primary_process_id
        assert primary_process_id == "Process_HelloWorld"

        process_models = ProcessModelService.get_process_models_for_api(user=user, recursive=True, filter_runnable_by_user=True)
        assert len(process_models) == 1
        assert process_model.primary_process_id == primary_process_id

        process_model = load_test_spec(
            "test_group/sample",
            bpmn_file_name="sample.bpmn",
            process_model_source_directory="sample",
        )

        # this model should not show up in results because it has no primary_file_name
        ProcessModelService.update_process_model(process_model, {"primary_file_name": None})
        process_models = ProcessModelService.get_process_models_for_api(user=user, recursive=True, filter_runnable_by_user=True)
        assert len(process_models) == 1

        process_model = load_test_spec(
            "non_executable/non_executable",
            bpmn_file_name="non_executable.bpmn",
            process_model_source_directory="non_executable",
        )

        # this model should not show up in results because it is not executable
        process_models = ProcessModelService.get_process_models_for_api(user=user, recursive=True, filter_runnable_by_user=True)
        assert len(process_models) == 1
