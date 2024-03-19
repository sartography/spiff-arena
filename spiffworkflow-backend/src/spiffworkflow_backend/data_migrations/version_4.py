from flask import current_app

# from SpiffWorkflow.bpmn.serializer.migration.version_1_3 import update_data_objects  # type: ignorefrom SpiffWorkflow.bpmn.serializer.migration.version_1_3 import update_data_objects  # type: ignore
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore
from spiffworkflow_backend.data_migrations.data_migration_base import DataMigrationBase
from spiffworkflow_backend.models.bpmn_process import BpmnProcessModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.task_service import TaskService
from sqlalchemy import or_


class Version4(DataMigrationBase):
    @classmethod
    def version(cls) -> str:
        return "4"

    @classmethod
    def run(cls, process_instance: ProcessInstanceModel) -> None:
        return None

        try:
            processor = ProcessInstanceProcessor(process_instance)
            bpmn_process_dict = processor.serialize()
            update_data_objects(bpmn_process_dict)
            bpmn_process_guids = list(bpmn_process_dict["subprocesses"].keys())
            bpmn_process_models = BpmnProcessModel.query.filter(
                or_(BpmnProcessModel.id == process_instance.bpmn_process_id, BpmnProcessModel.guid in bpmn_process_guids)
            ).all()

            new_json_data = []
            new_bpmn_models = []
            for bpm in bpmn_process_models:
                bpmn_dict = bpmn_process_dict["subprocesses"].get(bpm.guid)
                if bpmn_dict is None:
                    bpmn_dict = bpmn_process_dict
                new_data = bpmn_process_dict["data"]
                json_data_dict = TaskService.update_task_data_on_bpmn_process(bpm, new_data)
                if json_data_dict is not None:
                    new_json_data.append(json_data_dict)
                    new_bpmn_models.append(bpm)
                # bpm_definition = BpmnProcessDefinitionModel.query.filter_by(id=bpm.bpmn_process_definition_id).first()

            # for subprocess_dict in bpmn_process_dict['subprocesses']:

        except Exception as ex:
            current_app.logger.warning(f"Failed to migrate process_instance '{process_instance.id}'. The error was {str(ex)}")

    @classmethod
    def update_spiff_task_parents(cls, spiff_task: SpiffTask, task_service: TaskService) -> None:
        task_service.update_task_model_with_spiff_task(spiff_task)
        if spiff_task.parent is not None:
            cls.update_spiff_task_parents(spiff_task.parent, task_service)
