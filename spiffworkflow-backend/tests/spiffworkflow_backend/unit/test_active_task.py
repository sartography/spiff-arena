"""Process Model."""
from decimal import Decimal

from flask.app import Flask
from flask_bpmn.models.db import db

from spiffworkflow_backend.models.active_task import ActiveTaskModel
from spiffworkflow_backend.models.active_task_user import ActiveTaskUserModel
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec

from spiffworkflow_backend.models.spiff_logging import SpiffLoggingModel


class TestActiveTask(BaseTest):

    def test_can_create_and_delete_an_active_task (
        self, app: Flask, with_db_and_bpmn_file_cleanup: None
    ) -> None:
        process_model = load_test_spec(
            "call_activity_test",
            process_model_source_directory="call_activity_same_directory",
        )

        process_instance = self.create_process_instance_from_process_model(
            process_model
        )
        active_task = ActiveTaskModel(
            process_instance_id=process_instance.id,
            process_model_display_name="my shorts",
            form_file_name="my_file_name",
            ui_form_file_name="",
            task_id="1234",
            task_name="any old thing",
            task_title="",
            task_type="test type",
            task_status="WAITING",
            lane_assignment_id=None,
        )
        initiator_user = self.find_or_create_user("initiator_user")
        db.session.add(active_task)
        db.session.commit()
        active_task_user = ActiveTaskUserModel(active_task_id=active_task.id, user_id=initiator_user.id)
        db.session.add(active_task_user)
        db.session.commit()
        processor = ProcessInstanceProcessor(process_instance)
        processor.save()  # This should clear out all active tasks and active task users.
        assert(len(db.session.query(ActiveTaskModel).all()) == 0)