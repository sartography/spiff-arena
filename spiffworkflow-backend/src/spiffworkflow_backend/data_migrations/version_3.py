import copy

from flask import current_app
from spiffworkflow_backend.data_migrations.data_migration_base import DataMigrationBase
from spiffworkflow_backend.models.bpmn_process import BpmnProcessModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.task import TaskModel


class Version3(DataMigrationBase):
    @classmethod
    def version(cls) -> str:
        return "3"

    @classmethod
    def run(cls, process_instance: ProcessInstanceModel) -> None:
        try:
            tasks = TaskModel.query.filter_by(process_instance_id=process_instance.id)
            bpmn_process_ids = []
            for task_model in tasks:
                new_properties_json = copy.copy(task_model.properties_json)
                if "typename" not in new_properties_json or new_properties_json["typename"] != "Task":
                    new_properties_json["typename"] = "Task"
                    task_model.properties_json = new_properties_json
                    db.session.add(task_model)
                    bpmn_process_ids.append(task_model.bpmn_process_id)

            bpmn_processes = BpmnProcessModel.query.filter(BpmnProcessModel.id.in_(bpmn_process_ids))  # type: ignore
            for bpmn_process in bpmn_processes:
                new_properties_json = copy.copy(bpmn_process.properties_json)
                typename = "BpmnWorkflow"
                if bpmn_process.direct_parent_process_id is not None:
                    typename = "BpmnSubWorkflow"
                if "typename" not in new_properties_json or new_properties_json["typename"] != typename:
                    new_properties_json["typename"] = typename
                    bpmn_process.properties_json = new_properties_json
                    db.session.add(bpmn_process)

        except Exception as ex:
            current_app.logger.warning(f"Failed to migrate process_instance '{process_instance.id}'. The error was {str(ex)}")
