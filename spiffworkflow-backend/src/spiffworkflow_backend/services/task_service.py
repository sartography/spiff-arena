from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.task import TaskModel  # noqa: F401
from SpiffWorkflow.bpmn.serializer.workflow import BpmnWorkflowSerializer  # type: ignore
from SpiffWorkflow.task import TaskStateNames  # type: ignore
from SpiffWorkflow.task import Task as SpiffTask
from spiffworkflow_backend.models.json_data import JsonDataModel  # noqa: F401
from spiffworkflow_backend.models.db import db
from hashlib import sha256
import json


class TaskService():

    @classmethod
    def update_task_data_on_task_model(cls, task_model: TaskModel, task_data_dict: dict) -> None:
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
    def update_task_model_and_add_to_db_session(cls, task_model: TaskModel, spiff_task: SpiffTask, serializer: BpmnWorkflowSerializer) -> None:
        """Updates properties_json and data on given task_model.

        This will NOT update start_in_seconds or end_in_seconds.
        """
        new_properties_json = serializer.task_to_dict(spiff_task)
        task_model.properties_json = new_properties_json
        task_model.state = TaskStateNames[new_properties_json['state']]
        cls.update_task_data_on_task_model(task_model, spiff_task.data)
        db.session.add(task_model)

    @classmethod
    def find_or_create_task_model_from_spiff_task(cls, spiff_task: SpiffTask, process_instance: ProcessInstanceModel) -> TaskModel:
        spiff_task_guid = str(spiff_task.id)
        task_model: TaskModel = TaskModel.query.filter_by(guid=spiff_task_guid).first()
        # if task_model is None:
        #     task_model = TaskModel(guid=spiff_task_guid, bpmn_process_id=process_instance.bpmn_process_id)
        #     db.session.add(task_model)
        #     db.session.commit()
        return task_model
