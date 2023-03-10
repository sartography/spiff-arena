import json
from hashlib import sha256
from typing import Tuple
from typing import Any
from typing import Optional

from SpiffWorkflow.bpmn.serializer.workflow import BpmnWorkflowSerializer, BpmnWorkflow  # type: ignore
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
        task_data_json = json.dumps(task_data_dict, sort_keys=True).encode("utf8")
        task_data_hash = sha256(task_data_json).hexdigest()
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
        task_model.properties_json = new_properties_json
        task_model.state = TaskStateNames[new_properties_json["state"]]
        cls.update_task_data_on_task_model(task_model, spiff_task.data)
        db.session.add(task_model)

    @classmethod
    def find_or_create_task_model_from_spiff_task(
        cls, spiff_task: SpiffTask, process_instance: ProcessInstanceModel,
        serializer: BpmnWorkflowSerializer, add_bpmn_process: Any
    ) -> TaskModel:
        spiff_task_guid = str(spiff_task.id)
        task_model: Optional[TaskModel] = TaskModel.query.filter_by(
            guid=spiff_task_guid
        ).first()
        if task_model is None:
            bpmn_process = cls.task_bpmn_process(spiff_task, process_instance, serializer, add_bpmn_process)
            task_model = TaskModel.query.filter_by(
                guid=spiff_task_guid
            ).first()
            if task_model is None:
                task_model = TaskModel(
                    guid=spiff_task_guid, bpmn_process_id=bpmn_process.id
                )
                db.session.commit()
        return task_model

    @classmethod
    def task_subprocess(cls, spiff_task: SpiffTask) -> Optional[Tuple[str, BpmnWorkflow]]:
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
        cls, spiff_task: SpiffTask, process_instance: ProcessInstanceModel,
        serializer: BpmnWorkflowSerializer, add_bpmn_process: Any
    ) -> BpmnProcessModel:
        subprocess_guid, subprocess = cls.task_subprocess(spiff_task)
        if subprocess is None:
            # This is the top level workflow, which has no guid
            return process_instance.bpmn_process
        else:
            # import pdb; pdb.set_trace()
            bpmn_process: Optional[BpmnProcessModel] = BpmnProcessModel.query.filter_by(
                guid=subprocess_guid
            ).first()
            # import pdb; pdb.set_trace()
            if bpmn_process is None:
                bpmn_process = add_bpmn_process(serializer.workflow_to_dict(subprocess), process_instance.bpmn_process, subprocess_guid, add_tasks_if_new_bpmn_process=True)
                db.session.commit()
                # spiff_task_guid = str(spiff_task.id)
                # raise Exception(
                #     f"Could not find bpmn_process for task {spiff_task_guid}"
                # )
            return bpmn_process
