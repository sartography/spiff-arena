import json
from hashlib import sha256
from typing import Optional
from typing import Tuple

from SpiffWorkflow.bpmn.serializer.workflow import BpmnWorkflow  # type: ignore
from SpiffWorkflow.bpmn.serializer.workflow import BpmnWorkflowSerializer
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore
from SpiffWorkflow.task import TaskStateNames

from spiffworkflow_backend.models.bpmn_process import BpmnProcessModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.json_data import JsonDataModel  # noqa: F401
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.task import TaskModel  # noqa: F401


class TaskService:
    @classmethod
    def update_task_data_on_task_model(
        cls, task_model: TaskModel, task_data_dict: dict
    ) -> None:
        task_data_json = json.dumps(task_data_dict, sort_keys=True)
        task_data_hash = sha256(task_data_json.encode("utf8")).hexdigest()
        if task_model.json_data_hash != task_data_hash:
            json_data = (
                db.session.query(JsonDataModel.id)
                .filter_by(hash=task_data_hash)
                .first()
            )
            if json_data is None:
                json_data = JsonDataModel(hash=task_data_hash, data=task_data_dict)
                db.session.add(json_data)
            task_model.json_data_hash = task_data_hash

    @classmethod
    def update_task_model_and_add_to_db_session(
        cls,
        task_model: TaskModel,
        spiff_task: SpiffTask,
        serializer: BpmnWorkflowSerializer,
    ) -> None:
        """Updates properties_json and data on given task_model.

        This will NOT update start_in_seconds or end_in_seconds.
        """
        new_properties_json = serializer.task_to_dict(spiff_task)
        spiff_task_data = new_properties_json.pop("data")
        task_model.properties_json = new_properties_json
        task_model.state = TaskStateNames[new_properties_json["state"]]
        cls.update_task_data_on_task_model(task_model, spiff_task_data)
        db.session.add(task_model)

    @classmethod
    def find_or_create_task_model_from_spiff_task(
        cls,
        spiff_task: SpiffTask,
        process_instance: ProcessInstanceModel,
        serializer: BpmnWorkflowSerializer,
    ) -> TaskModel:
        spiff_task_guid = str(spiff_task.id)
        task_model: Optional[TaskModel] = TaskModel.query.filter_by(
            guid=spiff_task_guid
        ).first()
        if task_model is None:
            bpmn_process = cls.task_bpmn_process(
                spiff_task, process_instance, serializer
            )
            task_model = TaskModel.query.filter_by(guid=spiff_task_guid).first()
            if task_model is None:
                task_model = TaskModel(
                    guid=spiff_task_guid, bpmn_process_id=bpmn_process.id
                )
        return task_model

    @classmethod
    def task_subprocess(
        cls, spiff_task: SpiffTask
    ) -> Tuple[Optional[str], Optional[BpmnWorkflow]]:
        top_level_workflow = spiff_task.workflow._get_outermost_workflow()
        my_wf = spiff_task.workflow  # This is the workflow the spiff_task is part of
        my_sp = None
        my_sp_id = None
        if my_wf != top_level_workflow:
            # All the subprocesses are at the top level, so you can just compare them
            for sp_id, sp in top_level_workflow.subprocesses.items():
                if sp == my_wf:
                    my_sp = sp
                    my_sp_id = sp_id
                    break
        return (str(my_sp_id), my_sp)

    @classmethod
    def task_bpmn_process(
        cls,
        spiff_task: SpiffTask,
        process_instance: ProcessInstanceModel,
        serializer: BpmnWorkflowSerializer,
    ) -> BpmnProcessModel:
        subprocess_guid, subprocess = cls.task_subprocess(spiff_task)
        bpmn_process: Optional[BpmnProcessModel] = None
        if subprocess is None:
            bpmn_process = process_instance.bpmn_process
            # This is the top level workflow, which has no guid
            # check for bpmn_process_id because mypy doesn't realize bpmn_process can be None
            if process_instance.bpmn_process_id is None:
                bpmn_process = cls.add_bpmn_process(
                    serializer.workflow_to_dict(
                        spiff_task.workflow._get_outermost_workflow()
                    ),
                    process_instance,
                )
                db.session.commit()
        else:
            bpmn_process = BpmnProcessModel.query.filter_by(
                guid=subprocess_guid
            ).first()
            if bpmn_process is None:
                bpmn_process = cls.add_bpmn_process(
                    serializer.workflow_to_dict(subprocess),
                    process_instance,
                    process_instance.bpmn_process,
                    subprocess_guid,
                )
                db.session.commit()
        return bpmn_process

    @classmethod
    def add_bpmn_process(
        cls,
        bpmn_process_dict: dict,
        process_instance: ProcessInstanceModel,
        bpmn_process_parent: Optional[BpmnProcessModel] = None,
        bpmn_process_guid: Optional[str] = None,
    ) -> BpmnProcessModel:
        tasks = bpmn_process_dict.pop("tasks")
        bpmn_process_data_dict = bpmn_process_dict.pop("data")

        bpmn_process = None
        if bpmn_process_parent is not None:
            bpmn_process = BpmnProcessModel.query.filter_by(
                parent_process_id=bpmn_process_parent.id, guid=bpmn_process_guid
            ).first()
        elif process_instance.bpmn_process_id is not None:
            bpmn_process = process_instance.bpmn_process

        bpmn_process_is_new = False
        if bpmn_process is None:
            bpmn_process_is_new = True
            bpmn_process = BpmnProcessModel(guid=bpmn_process_guid)

        bpmn_process.properties_json = bpmn_process_dict

        bpmn_process_data_json = json.dumps(bpmn_process_data_dict, sort_keys=True)
        bpmn_process_data_hash = sha256(
            bpmn_process_data_json.encode("utf8")
        ).hexdigest()
        if bpmn_process.json_data_hash != bpmn_process_data_hash:
            json_data = (
                db.session.query(JsonDataModel.id)
                .filter_by(hash=bpmn_process_data_hash)
                .first()
            )
            if json_data is None:
                json_data = JsonDataModel(
                    hash=bpmn_process_data_hash, data=bpmn_process_data_dict
                )
                db.session.add(json_data)
            bpmn_process.json_data_hash = bpmn_process_data_hash

        if bpmn_process_parent is None:
            process_instance.bpmn_process = bpmn_process
        elif bpmn_process.parent_process_id is None:
            bpmn_process.parent_process_id = bpmn_process_parent.id
        db.session.add(bpmn_process)

        if bpmn_process_is_new:
            for task_id, task_properties in tasks.items():
                task_data_dict = task_properties.pop("data")
                state_int = task_properties["state"]

                task_model = TaskModel.query.filter_by(guid=task_id).first()
                if task_model is None:
                    # bpmn_process_identifier = task_properties['workflow_name']
                    # bpmn_identifier = task_properties['task_spec']
                    #
                    # task_definition = TaskDefinitionModel.query.filter_by(bpmn_identifier=bpmn_identifier)
                    # .join(BpmnProcessDefinitionModel).filter(BpmnProcessDefinitionModel.bpmn_identifier==bpmn_process_identifier).first()
                    # if task_definition is None:
                    #     subprocess_task = TaskModel.query.filter_by(guid=bpmn_process.guid)
                    task_model = TaskModel(
                        guid=task_id, bpmn_process_id=bpmn_process.id
                    )
                task_model.state = TaskStateNames[state_int]
                task_model.properties_json = task_properties

                TaskService.update_task_data_on_task_model(task_model, task_data_dict)
                db.session.add(task_model)

        return bpmn_process
