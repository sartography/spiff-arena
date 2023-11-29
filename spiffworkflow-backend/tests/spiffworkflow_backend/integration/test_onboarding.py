from flask import Flask
from flask.testing import FlaskClient
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.user import UserModel

from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestOnboarding(BaseTest):
    def test_returns_nothing_if_no_onboarding_model(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        results = client.get(
            "/v1.0/onboarding",
            headers=self.logged_in_headers(with_super_admin_user),
        )

        assert results.status_code == 200
        assert results.json == {}

    def set_up_onboarding(self, client: FlaskClient, with_super_admin_user: UserModel, file_location: str) -> None:
        process_group_id = "site-administration"
        process_model_id = "onboarding"
        bpmn_file_location = file_location
        self.create_group_and_model_with_bpmn(
            client,
            with_super_admin_user,
            process_group_id=process_group_id,
            process_model_id=process_model_id,
            bpmn_file_location=bpmn_file_location,
        )

    def test_returns_onboarding_if_onboarding_model(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        self.set_up_onboarding(client, with_super_admin_user, "onboarding")

        results = client.get(
            "/v1.0/onboarding",
            headers=self.logged_in_headers(with_super_admin_user),
        )

        assert results.status_code == 200
        assert len(results.json.keys()) == 4
        assert results.json["type"] == "default_view"
        assert results.json["value"] == "my_tasks"
        assert results.json["instructions"] == ""
        assert results.json["task_id"] is not None

        # Assure no residual process model is left behind if it executes and completes without additinal user tasks
        assert len(ProcessInstanceModel.query.all()) == 0

    def skip_test_persists_if_user_task_encountered(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """We are moving towards replacing the onboarding with Extensions
        so disabling this test, and the ability to start a person off on
        a workflow instantly on arrival."""
        self.set_up_onboarding(client, with_super_admin_user, "onboarding_with_user_task")
        results = client.get(
            "/v1.0/onboarding",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert results.status_code == 200
        assert len(results.json.keys()) == 4
        assert results.json["type"] == "user_input_required"
        assert results.json["process_instance_id"] is not None
        instance = ProcessInstanceModel.query.filter(ProcessInstanceModel.id == results.json["process_instance_id"]).first()
        assert instance is not None
