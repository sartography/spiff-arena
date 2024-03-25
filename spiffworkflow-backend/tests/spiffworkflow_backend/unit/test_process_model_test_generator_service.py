import os

from flask import json
from flask.app import Flask
from spiffworkflow_backend.services.file_system_service import FileSystemService
from spiffworkflow_backend.services.process_model_test_generator_service import ProcessModelTestGeneratorService
from spiffworkflow_backend.services.process_model_test_runner_service import ProcessModelTestRunner

from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestProcessModelTestGeneratorService(BaseTest):
    def test_can_generate_bpmn_unit_test_from_process_instance_json_and_run_it(
        self, app: Flask, with_db_and_bpmn_file_cleanup: None
    ) -> None:
        process_instance_json_file = self.get_test_file("process_model_test_importer.json")
        with open(process_instance_json_file) as f:
            process_instance_json = f.read()
        process_instance_dict = json.loads(process_instance_json)
        test_case_identifier = "our_test_case"

        bpmn_unit_test_specification = ProcessModelTestGeneratorService.generate_test_from_process_instance_dict(
            process_instance_dict, test_case_identifier=test_case_identifier
        )
        expected_specification = {
            test_case_identifier: {
                "tasks": {
                    "Process_sub_level:sub_manual_task": {"data": [{}]},
                    "call_activity_sub_process:sub_level_sub_process_user_task": {"data": [{"firstName": "Chuck"}]},
                    "Process_top_level:top_service_task": {
                        "data": [
                            {
                                "backend_status_response": {
                                    "body": '{"ok": true}',
                                    "mimetype": "application/json",
                                    "http_status": 200,
                                    "operator_identifier": "http/GetRequestV2",
                                }
                            }
                        ]
                    },
                },
                "expected_output_json": {
                    "firstName": "Chuck",
                    "data_objects": {"top_level_data_object": "a"},
                    "backend_status_response": {
                        "body": '{"ok": true}',
                        "mimetype": "application/json",
                        "http_status": 200,
                        "operator_identifier": "http/GetRequestV2",
                    },
                },
            }
        }
        assert expected_specification == bpmn_unit_test_specification

        process_model = load_test_spec(
            process_model_id="test_group/with-service-task-call-activity-sub-process",
            process_model_source_directory="with-service-task-call-activity-sub-process",
        )
        process_model_path = os.path.abspath(os.path.join(FileSystemService.root_path(), process_model.id_for_file_path()))
        with open(os.path.join(process_model_path, "test_main.json"), "w") as f:
            f.write(json.dumps(bpmn_unit_test_specification, indent=2))
        process_model_test_runner = ProcessModelTestRunner(
            process_model_directory_path=process_model_path,
            process_model_directory_for_test_discovery=process_model_path,
            test_case_file="test_main.json",
            test_case_identifier=test_case_identifier,
        )
        process_model_test_runner.run()

        results = process_model_test_runner.test_case_results[0]
        assert results.passed is True
