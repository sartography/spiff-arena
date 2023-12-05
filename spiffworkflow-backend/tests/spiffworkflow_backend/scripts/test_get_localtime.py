import datetime

import pytz
from flask.app import Flask
from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.get_localtime import GetLocaltime
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService

from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestGetLocaltime(BaseTest):
    def test_get_localtime_script_directly(self) -> None:
        current_time = datetime.datetime.now()
        timezone = "US/Pacific"
        process_model_identifier = "test_process_model"
        process_instance_id = 1
        script_attributes_context = ScriptAttributesContext(
            task=None,
            environment_identifier="testing",
            process_instance_id=process_instance_id,
            process_model_identifier=process_model_identifier,
        )
        result = GetLocaltime().run(
            script_attributes_context,
            datetime=current_time,
            timezone=timezone,
        )
        assert result == current_time.astimezone(pytz.timezone(timezone))

    def test_get_localtime_script_through_bpmn(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        initiator_user = self.find_or_create_user("initiator_user")
        self.add_permissions_to_user(
            initiator_user,
            target_uri="/v1.0/process-groups",
            permission_names=["read", "create"],
        )
        process_model = load_test_spec(
            process_model_id="test_group/get_localtime",
            bpmn_file_name="get_localtime.bpmn",
            process_model_source_directory="get_localtime",
        )
        process_instance = self.create_process_instance_from_process_model(process_model=process_model, user=initiator_user)
        processor = ProcessInstanceProcessor(process_instance)

        processor.do_engine_steps(save=True)
        human_task = process_instance.active_human_tasks[0]
        spiff_task = processor.__class__.get_task_by_bpmn_identifier(human_task.task_name, processor.bpmn_process_instance)

        ProcessInstanceService.complete_form_task(
            processor,
            spiff_task,
            {"timezone": "US/Pacific"},
            initiator_user,
            human_task,
        )

        human_task = process_instance.active_human_tasks[0]
        spiff_task = processor.__class__.get_task_by_bpmn_identifier(human_task.task_name, processor.bpmn_process_instance)

        assert spiff_task

        data = ProcessInstanceProcessor._default_script_engine.environment.last_result()
        some_time = data["some_time"]
        localtime = data["localtime"]
        timezone = data["timezone"]

        assert localtime == some_time.astimezone(pytz.timezone(timezone))
