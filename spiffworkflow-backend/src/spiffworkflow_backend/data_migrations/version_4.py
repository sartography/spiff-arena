from flask import current_app
from SpiffWorkflow.bpmn.serializer.migration.version_1_3 import update_data_objects  # type: ignore
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore
from spiffworkflow_backend.data_migrations.data_migration_base import DataMigrationBase
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.task_service import TaskService


class Version4(DataMigrationBase):
    @classmethod
    def version(cls) -> str:
        return "4"

    @classmethod
    def run(cls, process_instance: ProcessInstanceModel, should_raise_on_error: bool = False) -> None:
        try:
            processor = ProcessInstanceProcessor(
                process_instance, include_task_data_for_completed_tasks=True, include_completed_subprocesses=True
            )
            bpmn_process_dict = processor.serialize()
            update_data_objects(bpmn_process_dict)
            ProcessInstanceProcessor.persist_bpmn_process_dict(
                bpmn_process_dict,
                bpmn_definition_to_task_definitions_mappings={},
                process_instance_model=process_instance,
                store_process_instance_events=False,
            )

        except Exception as ex:
            if cls.should_raise_on_error():
                raise ex
            current_app.logger.warning(f"Failed to migrate process_instance '{process_instance.id}'. The error was {str(ex)}")

    @classmethod
    def update_spiff_task_parents(cls, spiff_task: SpiffTask, task_service: TaskService) -> None:
        task_service.update_task_model_with_spiff_task(spiff_task)
        if spiff_task.parent is not None:
            cls.update_spiff_task_parents(spiff_task.parent, task_service)
