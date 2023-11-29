from typing import Any

from flask.app import Flask
from flask.testing import FlaskClient
from spiffworkflow_backend import db
from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.routes.tasks_controller import _dequeued_interstitial_stream

from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestForGoodErrors(BaseTest):
    """Assure when certain errors happen when rendering a jinaj2 error that it makes some sense."""

    def test_invalid_form(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """React json form schema with bad jinja syntax provides good error."""
        process_model = load_test_spec(
            process_model_id="group/simple_form_with_error",
            process_model_source_directory="simple_form_with_error",
        )
        response = self.create_process_instance_from_process_model_id_with_api(
            client,
            # process_model.process_group_id,
            process_model.id,
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.json is not None
        process_instance_id = response.json["id"]
        response = client.post(
            f"/v1.0/process-instances/{self.modify_process_identifier_for_path_param(process_model.id)}/{process_instance_id}/run",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200
        response = self._get_next_user_task(process_instance_id, client, with_super_admin_user)
        assert response.json is not None
        assert response.json["error_type"] == "TemplateSyntaxError"
        assert response.json["line_number"] == 3
        assert response.json["file_name"] == "simple_form.json"

    def test_jinja2_error_message_for_end_user_instructions(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        process_model = load_test_spec(
            process_model_id="group/end_user_instructions_error",
            bpmn_file_name="instructions_error.bpmn",
            process_model_source_directory="error",
        )
        process_instance = self.create_process_instance_from_process_model(
            process_model=process_model, user=with_super_admin_user
        )

        response = client.post(
            f"/v1.0/process-instances/{self.modify_process_identifier_for_path_param(process_model.id)}/{process_instance.id}/run",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        response = self._get_next_user_task(process_instance.id, client, with_super_admin_user)

        assert response.status_code == 400
        assert response.json is not None
        assert response.json["error_type"] == "TemplateSyntaxError"
        assert response.json["line_number"] == 3
        assert response.json["error_line"] == "{{ x +=- 1}}"
        assert response.json["file_name"] == "instructions_error.bpmn"
        assert "instructions for end user" in response.json["message"]
        assert "Jinja2" in response.json["message"]
        assert "unexpected '='" in response.json["message"]

    def _get_next_user_task(
        self,
        process_instance_id: int,
        client: FlaskClient,
        with_super_admin_user: UserModel,
    ) -> Any:
        # Call this to assure all engine-steps are fully processed before we search for human tasks.
        _dequeued_interstitial_stream(process_instance_id)

        """Returns the next available user task for a given process instance, if possible."""
        human_tasks = db.session.query(HumanTaskModel).filter(HumanTaskModel.process_instance_id == process_instance_id).all()
        assert len(human_tasks) > 0, "No human tasks found for process."
        human_task = human_tasks[0]
        response = client.get(
            f"/v1.0/tasks/{process_instance_id}/{human_task.task_id}?with_form_data=true",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        return response
