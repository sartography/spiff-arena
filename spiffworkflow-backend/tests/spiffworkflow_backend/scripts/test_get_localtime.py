from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from flask.app import Flask
from flask.testing import FlaskClient
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.scripts.get_localtime import GetLocaltime
import datetime
import pytz

from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestGetLocaltime(BaseTest):
    """TestProcessAPi."""

    def test_get_localtime_script_directly(self):
        current_time = datetime.datetime.now()
        timezone = "US/Pacific"
        result = GetLocaltime().run(task=None, environment_identifier='testing', datetime=current_time, timezone=timezone)
        assert result == current_time.astimezone(pytz.timezone(timezone))

    def test_get_localtime_script_through_bpmn(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        """Test_process_instance_run."""
        initiator_user = self.find_or_create_user("initiator_user")
        process_model = load_test_spec(
            process_model_id="get_localtime", bpmn_file_name="get_localtime.bpmn"
        )
        process_instance = self.create_process_instance_from_process_model(
            process_model=process_model, user=initiator_user
        )
        processor = ProcessInstanceProcessor(process_instance)

        processor.do_engine_steps(save=True)
        active_task = process_instance.active_tasks[0]
        spiff_task = processor.__class__.get_task_by_bpmn_identifier(
            active_task.task_name, processor.bpmn_process_instance
        )

        ProcessInstanceService.complete_form_task(
            processor, spiff_task, {"timezone": "US/Pacific"}, initiator_user
        )

        active_task = process_instance.active_tasks[0]
        spiff_task = processor.__class__.get_task_by_bpmn_identifier(
            active_task.task_name, processor.bpmn_process_instance
        )

        data = spiff_task.data
        some_time = data['some_time']
        localtime = data['localtime']
        timezone = data['timezone']

        assert localtime == some_time.astimezone(pytz.timezone(timezone))
