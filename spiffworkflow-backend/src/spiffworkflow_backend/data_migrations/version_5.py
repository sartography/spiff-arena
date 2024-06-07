from spiffworkflow_backend.models.db import db
from flask import current_app
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore
from spiffworkflow_backend.data_migrations.data_migration_base import DataMigrationBase
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.task import TaskModel
from spiffworkflow_backend.models.task_definition import TaskDefinitionModel
from spiffworkflow_backend.services.task_service import TaskService


class Version5(DataMigrationBase):
    @classmethod
    def version(cls) -> str:
        return "5"

    @classmethod
    def run(cls, process_instance: ProcessInstanceModel) -> None:
        try:
            tasks = (
                TaskModel.query.filter_by(process_instance_id=process_instance.id, state="WAITING")
                .join(TaskDefinitionModel, TaskDefinitionModel.id == TaskModel.task_definition_id)
                .filter(
                    TaskDefinitionModel.typename
                    in ["SequentialMultiInstanceTask", "ParallelMultiInstanceTask", "StandardLoopTask"]
                )
                .all()
            )

            for task in tasks:
                task.state = "STARTED"
                db.session.add(task)
        except Exception as ex:
            current_app.logger.warning(f"Failed to migrate process_instance '{process_instance.id}'. The error was {str(ex)}")

    @classmethod
    def update_spiff_task_parents(cls, spiff_task: SpiffTask, task_service: TaskService) -> None:
        task_service.update_task_model_with_spiff_task(spiff_task)
        if spiff_task.parent is not None:
            cls.update_spiff_task_parents(spiff_task.parent, task_service)
