from flask import current_app
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.task_service import TaskService


class Version2:
    VERSION = "2"

    @classmethod
    def run(cls, process_instances: list[ProcessInstanceModel]) -> None:
        for process_instance in process_instances:
            try:
                processor = ProcessInstanceProcessor(process_instance)
                processor.bpmn_process_instance._predict()

                spiff_tasks = processor.bpmn_process_instance.get_tasks()
                task_service = TaskService(
                    process_instance, processor._serializer, processor.bpmn_definition_to_task_definitions_mappings
                )

                # implicit begin db transaction
                for spiff_task in spiff_tasks:
                    task_service.update_task_model_with_spiff_task(spiff_task)

                task_service.save_objects_to_database()
                process_instance.spiff_serializer_version = cls.VERSION
                db.session.add(process_instance)
                db.session.commit()
            except Exception as ex:
                current_app.logger.warning(
                    f"Failed to migrate process_instance '{process_instance.id}'. The error was {str(ex)}"
                )
