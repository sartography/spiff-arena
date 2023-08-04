from flask import Flask
from flask.testing import FlaskClient
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

    def test_returns_onboarding_if_onboarding_model(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        process_group_id = "site-administration"
        process_model_id = "onboarding"
        bpmn_file_location = "onboarding"
        self.create_group_and_model_with_bpmn(
            client,
            with_super_admin_user,
            process_group_id=process_group_id,
            process_model_id=process_model_id,
            bpmn_file_location=bpmn_file_location,
        )

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
