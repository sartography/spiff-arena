from SpiffWorkflow.bpmn.workflow import TaskState
import time
from SpiffWorkflow.task import Task as SpiffTask # type: ignore
from flask import current_app
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.task_service import TaskService


class Version2:
    VERSION = "2"

    @classmethod
    def run(cls, process_instance: ProcessInstanceModel) -> None:
        initial_time = time.time()
        try:
            processor = ProcessInstanceProcessor(process_instance)
            processor.bpmn_process_instance._predict()

            spiff_tasks = processor.bpmn_process_instance.get_tasks(updated_ts=initial_time)
            task_service = TaskService(
                process_instance, processor._serializer, processor.bpmn_definition_to_task_definitions_mappings
            )

            # implicit begin db transaction
            for spiff_task in spiff_tasks:
                cls.update_spiff_task_parents(spiff_task, task_service)

            task_service.save_objects_to_database()
        except Exception as ex:
            current_app.logger.warning(
                f"Failed to migrate process_instance '{process_instance.id}'. The error was {str(ex)}"
            )

    @classmethod
    def update_spiff_task_parents(cls, spiff_task: SpiffTask, task_service: TaskService) -> None:
        task_service.update_task_model_with_spiff_task(spiff_task)
        if spiff_task.parent is not None:
            cls.update_spiff_task_parents(spiff_task.parent, task_service)
