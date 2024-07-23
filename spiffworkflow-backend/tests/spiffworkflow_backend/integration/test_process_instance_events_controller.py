from flask.app import Flask
from flask.testing import FlaskClient
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance_event import ProcessInstanceEventType
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.process_instance_tmp_service import ProcessInstanceTmpService

from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestProcessInstanceEventsController(BaseTest):
    def test_process_instance_migration_event_list(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        process_model, process_instance_id = self.create_and_run_process_instance(
            client=client,
            user=with_super_admin_user,
            process_model_id="migration-test-with-subprocess",
            bpmn_file_name="migration-initial.bpmn",
        )
        process_instance = ProcessInstanceModel.query.filter_by(id=process_instance_id).first()
        assert process_instance is not None

        number_of_events = 3
        for ii in range(number_of_events):
            ProcessInstanceTmpService.add_event_to_process_instance(
                process_instance,
                ProcessInstanceEventType.process_instance_migrated.value,
                migration_details={
                    "initial_git_revision": f"rev{ii}",
                    "initial_bpmn_process_hash": f"hash{ii}",
                    "target_git_revision": f"rev{ii+1}",
                    "target_bpmn_process_hash": f"hash{ii+1}",
                },
            )
        # add random event to ensure it does not come back from api
        ProcessInstanceTmpService.add_event_to_process_instance(
            process_instance,
            ProcessInstanceEventType.process_instance_resumed.value,
        )

        response = client.get(
            f"/v1.0/process-instance-events/{process_model.modified_process_model_identifier()}/{process_instance.id}/migration",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200
        assert response.json
        events = response.json["results"]
        assert len(events) == number_of_events

        # events are returned newest first so reverse order to make checking easier
        events.reverse()
        for ii in range(number_of_events):
            assert events[ii]["initial_git_revision"] == f"rev{ii}"
            assert events[ii]["initial_bpmn_process_hash"] == f"hash{ii}"
            assert events[ii]["target_git_revision"] == f"rev{ii+1}"
            assert events[ii]["target_bpmn_process_hash"] == f"hash{ii+1}"
            assert events[ii]["username"] == with_super_admin_user.username
