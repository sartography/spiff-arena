from flask.app import Flask

from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestGetCurrentTaskData(BaseTest):
    def test_get_current_task_data_through_bpmn(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        initiator_user = self.find_or_create_user("initiator_user")
        process_model = load_test_spec(
            process_model_id="test_group/get_current_task_data",
            bpmn_file_name="get_current_task_data.bpmn",
            process_model_source_directory="get_current_task_data",
        )
        process_instance = self.create_process_instance_from_process_model(process_model=process_model, user=initiator_user)
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)

        data = ProcessInstanceProcessor._default_script_engine.environment.last_result()
        assert data["a"] == {"c": 3}
