from flask.app import Flask
from flask.testing import FlaskClient
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor

from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestJsonFileDataStore(BaseTest):
    def test_can_execute_diagram(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        process_model = load_test_spec(
            process_model_id="tests/data/json_file_data_store",
            process_model_source_directory="json_file_data_store",
        )
        process_instance = self.create_process_instance_from_process_model(process_model=process_model)
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps()

        assert "x" in processor.bpmn_process_instance.data

        result = processor.bpmn_process_instance.data["x"]

        assert result == {
            "company": "Some Job",
            "contact": "Sue Smith",
            "email": "sue@email.ai",
            "notes": "Decision Maker\nDoes'nt answer emails.",
        }
