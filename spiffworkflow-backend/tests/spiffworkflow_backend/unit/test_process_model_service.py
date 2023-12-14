import re

from flask import Flask
from spiffworkflow_backend.services.process_model_service import ProcessModelService

from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestProcessModelService(BaseTest):
    def test_can_update_specified_attributes(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_model = load_test_spec(
            "test_group/hello_world",
            bpmn_file_name="hello_world.bpmn",
            process_model_source_directory="hello_world",
        )
        assert process_model.display_name == "test_group/hello_world"

        primary_process_id = process_model.primary_process_id
        assert primary_process_id == "Process_HelloWorld"

        ProcessModelService.update_process_model(process_model, {"display_name": "new_name"})

        assert process_model.display_name == "new_name"
        assert process_model.primary_process_id == primary_process_id

    def test_can_get_file_contents(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_model = load_test_spec(
            "test_group/hello_world",
            bpmn_file_name="hello_world.bpmn",
            process_model_source_directory="hello_world",
        )
        assert process_model.display_name == "test_group/hello_world"

        primary_process_id = process_model.primary_process_id
        assert primary_process_id == "Process_HelloWorld"

        process_models = ProcessModelService.get_process_models(recursive=True, include_files=True)
        assert len(process_models) == 1

        pm_string = app.json.dumps(process_models[0])
        pm_dict = app.json.loads(pm_string)
        assert len(pm_dict["files"]) == 1
        file = pm_dict["files"][0]
        assert re.search("hello", file["file_contents"]) is not None

