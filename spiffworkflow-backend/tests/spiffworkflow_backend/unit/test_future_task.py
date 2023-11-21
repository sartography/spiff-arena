
import time
from spiffworkflow_backend.models.db import db

import pytest
from flask.app import Flask
from spiffworkflow_backend.models.future_task import FutureTaskModel
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor

from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestFutureTask(BaseTest):
    def test_can_add_record_from_bpmn_timer_event(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_model = load_test_spec(
            process_model_id="test_group/user-task-with-timer",
            process_model_source_directory="user-task-with-timer",
        )
        process_instance = self.create_process_instance_from_process_model(
            process_model=process_model
        )
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)
        assert process_instance.status == "user_input_required"

        future_tasks = FutureTaskModel.query.all()
        assert len(future_tasks) == 1
        future_task = future_tasks[0]
        ten_minutes_from_now = 10 * 60 + time.time()

        # give a 2 second leeway
        assert future_task.run_at_in_seconds == pytest.approx(ten_minutes_from_now, abs=2)

        twenty_minutes_from_now = round(20 * 60 + time.time())
        FutureTaskModel.insert_or_update(guid=future_task.guid, run_at_in_seconds=twenty_minutes_from_now)
        db.session.commit()
        assert future_task.run_at_in_seconds == pytest.approx(twenty_minutes_from_now, abs=2)
