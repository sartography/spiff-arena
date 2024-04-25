import json
import sys

from spiffworkflow_backend import create_app
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.task import TaskModel  # noqa: F401
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.user_service import UserService


def main(process_model_identifier: str, filepath: str, process_instance_id: int | None = None) -> None:
    app = create_app()
    with app.app_context():
        user = UserService.find_or_create_system_user()
        process_model = ProcessModelService.get_process_model(process_model_identifier.replace(":", "/"))
        if process_instance_id is not None:
            process_instance = ProcessInstanceModel.query.filter_by(id=process_instance_id).first()
        else:
            process_instance, _ = ProcessInstanceService.create_process_instance(process_model, user)

        if process_instance.process_model_identifier != process_model.id:
            raise Exception(
                f"Process model identifier '{process_model_identifier}' was passed in but process instance "
                f"{process_instance.id} has '{process_instance.process_model_identifier}'"
            )
        with open(filepath) as f:
            bpmn_process_json = f.read()
        bpmn_process_dict = json.loads(bpmn_process_json)

        if process_instance_id is None:
            task_guid_sample = list(bpmn_process_dict["tasks"].keys())[0]
            task_model = TaskModel.query.filter_by(guid=task_guid_sample).first()
            if task_model is not None:
                raise Exception(
                    "Tasks already exist in database for given json. "
                    "If you want to reset a process_instance then please pass in its id."
                )

        ProcessInstanceProcessor.persist_bpmn_process_dict(
            bpmn_process_dict, bpmn_definition_to_task_definitions_mappings={}, process_instance_model=process_instance
        )
        print(process_instance.id)


if len(sys.argv) < 3:
    raise Exception("usage: [script] [process_model_identifier] [bpmn_json_file_path]")

process_instance_id: int | None = None
if len(sys.argv) > 3:
    process_instance_id = int(sys.argv[3])

main(sys.argv[1], sys.argv[2], process_instance_id)
