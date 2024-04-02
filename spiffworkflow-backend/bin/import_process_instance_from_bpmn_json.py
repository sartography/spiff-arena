import json
import sys

from spiffworkflow_backend import create_app
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.user_service import UserService


def main(process_model_identifier: str, filepath: str) -> None:
    app = create_app()
    with app.app_context():
        user = UserService.find_or_create_system_user()
        process_model = ProcessModelService.get_process_model(process_model_identifier.replace(":", "/"))
        process_instance, _ = ProcessInstanceService.create_process_instance(process_model, user)
        with open(filepath) as f:
            bpmn_process_json = f.read()
        bpmn_process_dict = json.loads(bpmn_process_json)
        ProcessInstanceProcessor.persist_bpmn_process_dict(
            bpmn_process_dict, bpmn_definition_to_task_definitions_mappings={}, process_instance_model=process_instance
        )


if len(sys.argv) < 3:
    raise Exception("usage: [script] [process_model_identifier] [bpmn_json_file_path]")

main(sys.argv[1], sys.argv[2])
