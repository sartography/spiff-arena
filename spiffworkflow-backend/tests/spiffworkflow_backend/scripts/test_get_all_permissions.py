from operator import itemgetter

from flask.app import Flask
from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.get_all_permissions import GetAllPermissions
from spiffworkflow_backend.services.authorization_service import AuthorizationService

from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestGetAllPermissions(BaseTest):
    def test_can_get_all_permissions(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        # now that we have everything, try to clear it out...
        script_attributes_context = ScriptAttributesContext(
            task=None,
            environment_identifier="testing",
            process_instance_id=1,
            process_model_identifier="my_test_user",
        )
        AuthorizationService.add_permission_from_uri_or_macro(
            permission="start", target="PG:hey:group", group_identifier="my_test_group"
        )
        AuthorizationService.add_permission_from_uri_or_macro(permission="all", target="/tasks", group_identifier="my_test_group")

        expected_permissions = [
            {
                "group_identifier": "my_test_group",
                "uri": "/logs/hey:group:*",
                "permissions": ["read"],
            },
            {
                "group_identifier": "my_test_group",
                "uri": "/logs/typeahead-filter-values/hey:group:*",
                "permissions": ["read"],
            },
            {
                "group_identifier": "my_test_group",
                "uri": "/process-instance-events/hey:group:*",
                "permissions": ["read"],
            },
            {
                "group_identifier": "my_test_group",
                "uri": "/process-instances/hey:group:*",
                "permissions": ["create"],
            },
            {
                "group_identifier": "my_test_group",
                "uri": "/process-instances/for-me/hey:group:*",
                "permissions": ["read"],
            },
            {
                "group_identifier": "my_test_group",
                "uri": "/tasks",
                "permissions": ["create", "read", "update", "delete"],
            },
            {
                "group_identifier": "my_test_group",
                "uri": "/process-data-file-download/hey:group:*",
                "permissions": ["read"],
            },
            {
                "group_identifier": "my_test_group",
                "uri": "/event-error-details/hey:group:*",
                "permissions": ["read"],
            },
        ]

        permissions = GetAllPermissions().run(script_attributes_context)
        sorted_permissions = sorted(permissions, key=itemgetter("uri"))
        sorted_expected_permissions = sorted(expected_permissions, key=itemgetter("uri"))
        assert sorted_permissions == sorted_expected_permissions
