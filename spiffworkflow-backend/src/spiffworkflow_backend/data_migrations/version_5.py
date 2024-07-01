import copy

from flask import current_app
from SpiffWorkflow.util.task import TaskState  # type: ignore
from spiffworkflow_backend.data_migrations.data_migration_base import DataMigrationBase
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.task import TaskModel
from spiffworkflow_backend.models.task_definition import TaskDefinitionModel


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
                    TaskDefinitionModel.typename.in_(  # type: ignore
                        ["SequentialMultiInstanceTask", "ParallelMultiInstanceTask", "StandardLoopTask"]
                    )
                )
                .all()
            )

            for task in tasks:
                task.state = "STARTED"
                new_properties_json = copy.copy(task.properties_json)
                new_properties_json["state"] = TaskState.STARTED
                task.properties_json = new_properties_json
                db.session.add(task)
        except Exception as ex:
            if cls.should_raise_on_error():
                raise ex
            current_app.logger.warning(f"Failed to migrate process_instance '{process_instance.id}'. The error was {str(ex)}")
