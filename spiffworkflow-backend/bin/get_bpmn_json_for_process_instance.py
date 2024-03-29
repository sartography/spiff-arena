import sys

from spiffworkflow_backend import create_app
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor


def main(process_instance_id: str) -> None:
    """Main."""
    app = create_app()
    with app.app_context():
        process_instance = ProcessInstanceModel.query.filter_by(id=process_instance_id).first()

        file_path = f"/var/tmp/{process_instance_id}_bpmn_json.json"  # noqa: S108
        if not process_instance:
            raise Exception(f"Could not find a process instance with id: {process_instance_id}")

        processor = ProcessInstanceProcessor(process_instance)
        processor.dump_to_disk(file_path)
        print(f"Saved to {file_path}")


if len(sys.argv) < 2:
    raise Exception("Process instance id not supplied")

main(sys.argv[1])
